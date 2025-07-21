import os
import re
import json
import time
import datetime
import requests
import socket
import logging
import threading
from sqlalchemy.orm.session import Session
from Test.data.session_mgr import open_session
from Test.data.tables.tables import (
    main_extra_info,
    sample_process,
    lismaininfo,
    labqflag,
    labmain
)
from Test.service.sample.sample_service_itemresult import SampleServiceItemResult
from Test.service.sample.sample_service_patient import SampleServicePatient, SamplePatientQueryParams
from openai import OpenAI
from Test.service.util import multi_filter
from Test.service.labcode_service import LabcodeService
from Test.service.settings.settings_service import SettingsService
from Test.service.comm.record_identify.record_identify import record_identify_dir
from Test.service.redis_instance import RedisInstance
from Test.service.settings.setting_identify import setting_identify_dir
from Test.config.Test_config import TestConfig


class Common(object):

    ai_lock = threading.RLock()
    ai_tasks = []

    _loop_interval_secs = 3  # 3秒

    @classmethod
    def start_thread(cls):
        def _loop_proc():
            while True:
                cls._process_ai_task()
                time.sleep(cls._loop_interval_secs)

        t = threading.Thread(target=_loop_proc, daemon=True)
        t.start()

    @classmethod
    def enqueue_ai_task(
            cls,
            sampleda: str,
            sampleno: str,
            source: str,
            model: str,
            process_immediately: bool = False
    ):
        cls.ai_lock.acquire()
        try:
            instrument = TestConfig.get_Test_instrument()
            
            # 如果sampleda是datetime类型，转换为字符串
            if hasattr(sampleda, 'strftime'):
                sampleda = sampleda.strftime('%Y-%m-%d')
            
            data = {
                "instrument": instrument,
                "sample_date": sampleda,
                "sample_no": sampleno,
                "source": source
            }
            
            for task in cls.ai_tasks:
                if task['sample_date'] == sampleda and task['sample_no'] == sampleno:
                    logging.info(f'跳过重复诊断任务: sample_date={sampleda}, sample_no={sampleno}')
                    return
                
            cls.ai_tasks.append(data)
            logging.info(f'enqueue ai task: {data}')
        finally:
            cls.ai_lock.release()

    @classmethod
    def get_ai_tasks(cls):
        return cls.ai_tasks
    
    @classmethod
    def _process_ai_task(cls):
        try:

            with open_session() as sess:

                auto_diagnose_unaccept = (SettingsService.get_value(sess, '/ai/auto_diagnose_unaccept') == '1')
                only_diagnose_complete_sample = (SettingsService.get_value(sess, '/ai/only_diagnose_complete_sample') == '1')
                
                tasks_to_remove = []
                for task in cls.ai_tasks:

                    tasks_to_remove.append(task)

                    sampleno = task['sample_no']
                    sampleda = task['sample_date']
                    instrument = task['instrument']
                    source = task['source']

                    if source == 'from_record_proc':
                        q = sess.query(labmain)
                        q = multi_filter(q, [
                            labmain.sampleno == sampleno,
                            labmain.sampleda == sampleda,
                            labmain.instrument == instrument
                        ])
                        sample = q.first()
                        if sample:
                            if auto_diagnose_unaccept and sample.resultflag == '9':
                                if only_diagnose_complete_sample:
                                    KEY_SAMPLE_CODES_LEFT = f"key_sample_codes_left_{sampleno}"
                                    codes = RedisInstance.get_redis_cache().get(KEY_SAMPLE_CODES_LEFT, [])
                                    codes = list(set(codes))

                                    complete = True
                                    for code in codes:
                                        if code in ["CBC", "DIFF", "RET", "PLT-F", "WPC", 'SP', 'CRP', 'SAA', 'ESR', 'A1C']:
                                            complete = False

                                    if not complete:
                                        continue
                            else:
                                continue
                        else:
                            continue

                    TongYi.call_tongyi_qianwen_api(task)
                    logging.info(f'process ai task: {task}')
            
        except Exception as e:
            logging.error(f"_process_ai_task error: {str(e)}")
        
        finally:
            cls.ai_lock.acquire()
            for task in tasks_to_remove:
                cls.ai_tasks.remove(task)
            cls.ai_lock.release()

    @classmethod
    def is_ai_port_open(cls, sess: Session, timeout=3):

        ai_service_url = SettingsService.get_value(sess, '/ai/ai_service_url')
        if not ai_service_url:
            return False, None

        host, port = ai_service_url.split(':')
        # host = '10.32.137.213'
        # port = 11434
        sock = None
        try:
            port = int(port)
            socket.setdefaulttimeout(timeout)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex((host, port))  # 尝试连接端口
            if result == 0:
                return True, ai_service_url
            else:
                return False, ai_service_url
        except Exception as e:
            return False, ai_service_url
        finally:
            socket.setdefaulttimeout(None)  # 恢复默认的超时设置
            if sock:
                sock.close()

    @classmethod
    def get_ai_model(cls, sess: Session, url=None):
        models = []
        # if cls.is_ai_port_open(sess):
        try:

            if url is None:
                ai_service_url = SettingsService.get_value(sess, '/ai/ai_service_url')
            else:
                ai_service_url = url

            if not ai_service_url:
                return []

            url = f'http://{ai_service_url}/api/tags'
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            models_ = data.get('models')
            models = [{'value':r.get('name')} for r in models_]

            data_dir = setting_identify_dir

            settings_file_path = os.path.join(data_dir, 'settings_schema_11_ai.json')
            with open(settings_file_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            # 找到并更新 ai_service_model 的 value_options
            for module in settings['modules']:
                if module['name'] == 'ai':
                    for child in module['children']:
                        if child['name'] == 'ai_service_model':
                            child['value_options'] = models
                            break

            # 写回文件
            with open(settings_file_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)

        except Exception as e:
            models = []
            logging.error(f"获取AI模型失败: {str(e)}")
        return models

    @classmethod
    def get_ai_diagnose(cls, sess: Session, params):
        sampleda, sampleno = params["sample_date"], params["sample_no"]
        
        # 检查是否在待处理任务中
        for task in cls.ai_tasks:
            if task['sample_date'] == sampleda and task['sample_no'] == sampleno:
                return {
                    'status': 'pending',
                    'text': None
                }
        
        q = sess.query(main_extra_info)
        query = q.filter(
            main_extra_info.sampleda == sampleda,
            main_extra_info.sampleno == sampleno,
            main_extra_info.seqno == 1
            ).first()

        if query:
            # 移除<think>标签及其内容
            # cleaned_diagnose = cls.remove_think_tags(query.di_diagnose)
            cleaned_diagnose = query.di_diagnose
            
            content = {
                'status': 'success',
                'text': cleaned_diagnose
            }
        else:
            content = {
                'status': 'error',
                'text': None
            }

        return content

    @classmethod
    def del_ai_diagnose(cls, sess: Session, params):
        sampleda, sampleno = params["sample_date"], params["sample_no"]
        q = sess.query(main_extra_info)
        query = q.filter(
            main_extra_info.sampleda == sampleda,
            main_extra_info.sampleno == sampleno,
            main_extra_info.seqno == 1
            )

        if query:
            query.delete()
            sess.commit()

        return True
    
    @classmethod
    def remove_think_tags(cls, text):
        """
        移除文本中的<think>标签及其内容
        """
        if text is None:
            return None
        
        # 使用非贪婪匹配模式移除所有<think>...</think>标签及其内容
        cleaned_text = re.sub(r'<think>[\s\S]*?<\/think>', '', text, flags=re.DOTALL)
        return cleaned_text

    @classmethod
    def get_tat_sample(cls, sess: Session, params):
        sampleda, sampleno = params["sample_date"], params["sample_no"]
        sampleda_time = datetime.datetime.strptime(sampleda, "%Y-%m-%d")
        new_date = sampleda_time + datetime.timedelta(days=1)
        q = sess.query(sample_process)
        q = q.filter(sample_process.sampleno == sampleno)
        q = q.filter(sample_process.record_time >= sampleda_time)
        q = q.filter(sample_process.record_time <= new_date)

        ret = q.all()
        rets = []
        for i in ret:
            rets.append({
                "record_time": i.record_time,
                "sampleno": i.sampleno,
                "record_source": i.record_source,
                "serialno": i.serialno,
                "record_type": i.record_type,
                "rack": i.rack,
                "tube": i.tube,
                "instrument_time": i.instrument_time,
                "item": i.item,
                "area": i.area,
                "store": i.store,
                "lisno": i.lisno,
                "sort_reason": i.sort_reason
            })

        return rets

    @classmethod
    def set_ai_diagnose(cls, sess: Session, params: SamplePatientQueryParams, query_info: str, diagnose: str):
        sampleda, sampleno = params.sample_date, params.sample_no
        q = sess.query(main_extra_info)
        r = q.filter(main_extra_info.sampleda == sampleda, main_extra_info.sampleno == sampleno).first()

        if r:
            r.di_diagnose = diagnose
            r.di_description = query_info
            sess.commit()
        else:
            r = main_extra_info()
            r.sampleda = sampleda
            r.sampleno = sampleno
            r.seqno = 1
            r.di_diagnose = diagnose
            r.di_description = query_info
            sess.add(r)
            sess.commit()

        return True


class TongYi(object):
    @classmethod
    def call_tongyi_qianwen_api(cls, params):

        with open_session() as sess:

            params_ = SamplePatientQueryParams()
            params_.__dict__.update(params)

            patient = SampleServicePatient.query_patient(sess, params_)
            code_items = LabcodeService.get_code_items(
                sess, ['DG', 'DP', 'BT', 'PT'], as_dict=True, with_extra=True
            )

            results = SampleServiceItemResult.query_item_results(sess, params_)

            item_results = results["item_results"]
            sample_items = results["sample_items"]

            results_ = []
            for item in item_results:
                itemno = item['item_no']
                srcresult = item['srcresult']
                unit = item['item_unit']
                group = item['item_group']
                bk = item['item_bk']

                if group == '' or group is None:
                    # 检查是否为AI相关的记录，忽略大小写
                    if not bk or bk.strip().upper() != 'AI':
                        continue  # 如果不是AI相关记录，跳过此条记录

                if srcresult == '----':
                    srcresult = '检测失败'

                try:
                    ref = sample_items.get(itemno)

                    itemna = ref.get('item_name')
                    if itemna == itemno:
                        item = itemno
                    else:
                        item = f"{itemno}({itemna})"
                    results_.append(f"{item}: {srcresult} {unit}")

                    if ref:
                        final_ref = ref.get('final_ref')
                        if final_ref:
                            lowlmt = final_ref.get('lowlmt')
                            uplmt = final_ref.get('uplmt')

                            if lowlmt is None and uplmt is None:
                                continue

                            # 尝试将结果转换为数值进行比较
                            try:
                                # 移除可能的单位和其他非数字字符
                                numeric_result = float(''.join(c for c in srcresult if c.isdigit() or c == '.' or c == '-'))
                                
                                # 比较结果与参考范围
                                status = ""
                                if lowlmt is not None and numeric_result < float(lowlmt):
                                    status = "↓(偏低)"
                                elif uplmt is not None and numeric_result > float(uplmt):
                                    status = "↑(偏高)"
                                else:
                                    status = "✓(正常)"
                                    
                                _t = f"{item}:{srcresult}  {unit} {status} 参考值:[{lowlmt}-{uplmt}]"
                            except (ValueError, TypeError):
                                # 如果无法转换为数值，则不添加状态标记
                                _t = f"{item}:{srcresult}  {unit} 参考值:[{lowlmt}-{uplmt}]"
                            
                            results_.pop()
                            results_.append(_t)
                except Exception as e:
                    # logging.error(f"处理项目结果时出错: {str(e)}")
                    pass

            if len(results_) > 0:
                result_info = ','.join(results_)

                q = sess.query(lismaininfo)
                q = multi_filter(
                    q,
                    [
                        lismaininfo.instrno == params_.instrument,
                        lismaininfo.sampleda == params_.sample_date,
                        lismaininfo.sampleno == params_.sample_no,
                    ],
                )

                ip_messages = q.all()

                ips = [r.val1 for r in ip_messages]

                q = sess.query(labqflag)
                q = multi_filter(
                    q,
                    [
                        labqflag.instrument == params_.instrument,
                        labqflag.sampleda == params_.sample_date,
                        labqflag.sampleno == params_.sample_no,
                    ],
                )

                labqflags = q.all()
                labqflag_info = [f"{r.qname}:{r.qresult}" for r in labqflags if r.qresult > 100]

                patient_info = ''
                sex = patient.get('sex')
                if sex is not None:
                    if sex == '1':
                        sex = '男'
                    elif sex == '2':
                        sex = '女'

                    patient_info = f"患者{ sex },"

                age = patient.get('patage')
                if age is not None:
                    age_unit = patient.get('ageunit')
                    if age_unit == '1':
                        age_unit = '岁'
                    elif age_unit == '2':
                        age_unit = '月'
                    elif age_unit == '3':
                        age_unit = '天'

                    patient_info += f"年龄{ age }{ age_unit },"
    
                dg = code_items['DG']
                dp = code_items['DP']

                dg_name_ = dg.get(patient.get('diagnose'), {})
                dg_name = dg_name_.get('codename')
                dp_name_ = dp.get(patient.get('srcdepno'), {})
                dp_name = dp_name_.get('codename')

                if dg_name:
                    patient_info += f"临床诊断:{ dg_name },"
                if dp_name:
                    patient_info += f"就诊科室:{ dp_name };"

                # 定义换行符变量
                nl = '\n'

                # 在f-string中使用变量
                query_info = f"""
                患者基本信息:
                {patient_info}

                检测结果:
                {nl.join(results_)}

                报警信息:
                {nl.join(ips)}

                Qflag值:
                {nl.join(labqflag_info)}
                """

                query_info = cls.create_medical_prompt(query_info)

                cv_id = str(time.time())

                ai_service_url = SettingsService.get_value(sess, '/ai/ai_service_url')
                ai_model = SettingsService.get_value(sess, '/ai/ai_service_model')

            start_time = int(time.time())

        try:
            client = OpenAI(
                base_url=f"http://{ai_service_url}/v1/",
                # 深度推理模型耗费时间会较长,建议您设置一个较长的超时时间,推荐为30分钟
                timeout=1800,
            )
            response = client.chat.completions.create(
                # 替换 <Model> 为模型的Model ID
                # model="deepseek-r1:32b",
                model=ai_model,
                messages=[
                    {"role": "user", "content": query_info}
                ],
                temperature=0
            )

            # 获取原始响应内容
            r = response.choices[0].message.content
            
            # 获取令牌计数
            if hasattr(response, 'usage') and hasattr(response.usage, 'completion_tokens'):
                # OpenAI格式
                completion_tokens = response.usage.completion_tokens
            else:
                # 尝试从其他属性获取
                completion_tokens = 0

            current_time = int(time.time())
            duration_seconds =  current_time - start_time

            # 计算并打印每秒令牌数
            tokens_per_second = completion_tokens / duration_seconds
            
            logging.info(f"Token生成速率: {tokens_per_second:.2f} tokens/s")

            # 移除空白行（保留有实际内容的行）
            if r:
                lines = r.splitlines()
                non_empty_lines = [line for line in lines if line.strip()]
                r = '\n'.join(non_empty_lines)

            content = {
                'text': r,
                'status': 'success'
            }

            with open_session() as sess:
                Common.set_ai_diagnose(sess, params_, query_info, r)
                sess.commit()

            msg = {
                "rack": "000000",
                "tube": "00",
                "sample_no": params_.sample_no,
                "sampleda": params_.sample_date,
                "position": "AI诊断",
                "instrument": params_.instrument,
                "ai_diagnose": r
            }
            RedisInstance.get_redis_mq().publish("online", msg)
            
        except Exception as err:
            logging.error(f'API调用错误: {err}')
            content = {
                'text': f'API调用失败: {str(err)}',
                'status': 'error'
            }
        else:
            content = {
                'text': '无结果',
                'status': 'error'
            }

        return content

    @classmethod
    def create_medical_prompt(cls, patient_info):
        """
        创建结构化的医学诊断提示
        尝试从当前exe目录下加载prompt文件，如果不存在则使用默认提示词
        """

        default_prompt = """
            您是一位检验科医生，请根据以下病人信息和检验结果进行分析，提示出异常信息并将建议汇报给临床医生。
            分析结果请根据《医学检验项目选择与临床应用》和《血细胞分析报告规范化指南》给出。
            请注意以上信息不要在思考过程和分析结果中透露。

            病人信息如下：
            -----------------------------------
            {patient_info}
            -----------------------------------

            分析结果需要提供以下内容：
            1. 异常指标解读
            2. 临床报告内容
            """
        
        data_dir = record_identify_dir

        # 尝试加载prompt文件
        prompt_file_path = os.path.join(data_dir, 'medical_prompt.txt')
        
        try:
            if os.path.exists(prompt_file_path):
                # 如果文件存在，读取文件内容作为prompt
                with open(prompt_file_path, 'r', encoding='utf-8') as f:
                    prompt_template = f.read()
            else:
                # 如果文件不存在，使用默认prompt
                prompt_template = default_prompt
        except Exception as e:
            # 如果读取文件出错，使用默认prompt并记录错误
            logging.error(f"读取医学提示词文件出错: {str(e)}，使用默认提示词")
            prompt_template = default_prompt

        # 格式化prompt，插入病人信息
        return prompt_template.format(patient_info=patient_info)