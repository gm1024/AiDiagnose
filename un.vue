<template>
  <div ref="root_div" id="root_div">
    <div class="body_div_wrap" style="overflow: hidden">
      <div class="body_div">
        <div
          class="vertical_panel with_padding_left"
          :style="'width: ' + left_col_width + 'px; overflow: auto'"
        >
          <SampleLocator ref="sample_locator" @filter_change="handlerFilterChange" />
          <br />
          <hr />
          <PatientInfo
            ref="patient_info"
            :width="left_col_width - 30 + 'px'"
            @saved="handlePatientInfoSaved"
          />
          <br />
          <hr />
          <PatientCheckResult ref="patient_chk_result" width="100%" />
        </div>

        <div class="vertical_panel with_padding_left" :style="'width: ' + middel_col_width + 'px'">
          <ItemResultGrid
            :show_prtflag="true"
            :show_unit="false"
            :show_actions="true"
            :show_results_no_item="true"
            ref="item_result_grid"
          ></ItemResultGrid>
        </div>

        <div
          id="right_panel"
          class="vertical_panel with_padding_left"
          :style="'width: ' + right_col_width + 'px; overflow: auto'"
        >
          <div style="background-color: white; padding: 25px">
            <Tabs type="card" ref="tabs">
              <TabPane key="list" :forceRender="true">
                <template #tab>
                  <span>
                    <OrderedListOutlined />
                    {{ t('general.tab.list') }}
                  </span>
                </template>

                <SampleList
                  target_table="labvwmainquery"
                  :toolbar="true"
                  :paging_mode="false"
                  :custom_columns="true"
                  :has_chk="true"
                  :auto_refresh="true"
                  ref="sample_list"
                  @row_change="handleRowChange"
                ></SampleList>
              </TabPane>
              <TabPane key="graph" :forceRender="true">
                <template #tab>
                  <span>
                    <LineChartOutlined />
                    {{ t('general.tab.graph') }}
                  </span>
                </template>

                <SampleGraph ref="sample_graph" :only_today="false" />
              </TabPane>
              <TabPane key="compare" :forceRender="true" :tab="t('general.tab.compare')">
                <CompareRounds ref="compare_rounds" />
              </TabPane>
              <TabPane key="log" :forceRender="true" :tab="t('general.tab.transport')">
                <HisLog ref="his_log" @trust_change="handleTrustChange" />
              </TabPane>
              <TabPane key="action_qflag" :forceRender="true" tab="Action & Qflag">
                <ActionQflag ref="action_qflag" />
              </TabPane>
              <TabPane key="not_accept" :forceRender="true" :tab="t('general.tab.reason')">
                <NotAcceptList ref="not_accept_list" />
              </TabPane>
            </Tabs>
          </div>
        </div>
      </div>
      <div style="clear: both"></div>
    </div>
    
    <div style="clear: both"></div>
    <div class="footer_div">
      <div class="bottom_buttons">
        <vxe-button size="mini" @click="toggleFloatWindow_graph">
          <LineChartOutlined twoToneColor="#52c41a" /> {{ t('general.tab.graph') }}
        </vxe-button>
        <vxe-button size="mini" @click="toggleFloatWindow_ipmsg">
          <AlertOutlined /> {{ t('general.tab.ip') }}
        </vxe-button>

        <vxe-button 
          size="mini" 
          @click="toggleFloatWindow_ai" 
          :disabled="!ai_port_avaliable" 
          v-if="ai_service_start"
          status="primary">
          <CloudOutlined /> 
          {{ ai_button_status }}
        </vxe-button>

        <div style="float: right; padding-right: 15px">
          <vxe-button status="primary" :disabled="!hasSample" size="mini" @click="handleGoPrev">
            {{ t('general.tab.pervious') }}(<ArrowUpOutlined />)
          </vxe-button>
          <vxe-button status="primary" :disabled="!hasSample" size="mini" @click="handleGoNext">
            {{ t('general.tab.next') }}(<ArrowDownOutlined />)
          </vxe-button>

          <Popconfirm
            :title="t('general.patient.chooseManualV')"
            :ok-text="t('general.patient.yes')"
            :cancel-text="t('general.patient.no')"
            @confirm="handleManualPass"
          >
            <vxe-button :disabled="!hasSample" size="mini">{{ t('general.tab.manualValidate') }}(F8)</vxe-button>
          </Popconfirm>
          <Popconfirm
            :title="t('general.patient.chooseManualI')"
            :ok-text="t('general.patient.yes')"
            :cancel-text="t('general.patient.no')"
            @confirm="handleManualNotPass"
          >
            <vxe-button :disabled="!hasSample" size="mini">{{ t('general.tab.manualUnvalidate') }}(F9)</vxe-button>
          </Popconfirm>

          <vxe-button :disabled="!hasSample" size="mini" @click="handleSecondVerify">
            {{ t('general.tab.micro') }}
          </vxe-button>

          <vxe-button :disabled="!hasSample" size="mini" @click="handleCdfOut">{{ t('general.tab.cdf_out') }}</vxe-button>

          <Dropdown :disabled="!hasSample" trigger="click">
            <template #overlay>
              <Menu @click="handlePrintClick">
                <MenuItem key="preview"> {{ t('general.tab.preview') }} </MenuItem>
                <MenuItem key="print"> {{ t('general.tab.printDirectly') }}( </MenuItem>
              </Menu>
            </template>
            <vxe-button size="mini">
              {{ t('general.tab.print') }}
              <DownOutlined />
            </vxe-button>
          </Dropdown>
        </div>
      </div>
    </div>

    <DescriptionEditor ref="desc_edt" :title="t('general.patient.microremark')" @on_changed="handleDescChanged" />

    <vxe-modal
      ref="floatwindow_graph"
      v-model="floatwindow_graph_visible"
      id="floatwindow_graph"
      width="680"
      height="400"
      min-width="400"
      min-height="320"
      size="mini"
      :zIndex=1600
      :mask="false"
      :lock-view="false"
      :lock-scroll="false"
      :marginSize="-500"
      resize
      remember
      storage
    >
      <template #title>
        <span>{{ t('general.tab.graph') }}</span>
      </template>
      <template #default>
        <div>
          <SampleGraph ref="sample_graph_float" :only_today="true" />
        </div>
      </template>
    </vxe-modal>

    <vxe-modal
      ref="floatwindow_ipmsg"
      v-model="floatwindow_ipmsg_visible"
      id="floatwindow_ipmsg"
      width="500"
      height="500"
      min-width="500"
      min-height="500"
      size="mini"
      :zIndex=1600
      :mask="false"
      :lock-view="false"
      :lock-scroll="false"
      :marginSize="-500"
      resize
      remember
      storage
      transfer
      @show="handleFloatWindowShow"
      @zoom="handleFloatWindowZoom"
    >
      <template #title>
        <span>{{ t('general.tab.ip') }}</span>
      </template>
      <template #default>
        <div>
          <IpMessage ref="ip_message_float" root_div_id="ip_message_float" />
        </div>
      </template>
    </vxe-modal>

    <vxe-modal
      ref="floatwindow_ai"
      v-model="floatwindow_ai_visible"
      id="floatwindow_ai"
      width="500"
      height="500"
      min-width="500"
      min-height="500"
      size="mini"
      :zIndex=1600
      :mask="false"
      :lock-view="false"
      :lock-scroll="false"
      :marginSize="-500"
      resize
      remember
      storage
      transfer
      @show="handleFloatWindowShow"
      @zoom="handleFloatWindowZoom"
    >
      <template #title>
        <span>{{ t('general.patient.Aidiagnostic') }}</span>
      </template>
      <template #default>
        <div class="markdown-content">
          <div v-html="renderMarkdown(ai_diagnose_text)"></div>
        </div>
      </template>
    </vxe-modal>

    <SamplePrint ref="print_preview_dlg" />

  </div>
</template>

<script lang="ts">
import { debounce } from 'lodash';
import {
  defineComponent,
  ref,
  onMounted,
  onBeforeUnmount,
  onActivated,
  onDeactivated,
  reactive,
  nextTick,
} from 'vue';
import {
  Row,
  Col,
  Card,
  Button,
  Drawer,
  Tabs,
  TabPane,
  Popconfirm,
  Dropdown,
  Menu,
  MenuItem,
  Spin,
  Alert,
  message,
  Modal,
} from 'ant-design-vue';

import {
  LineChartOutlined,
  AlertOutlined,
  OrderedListOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  DownOutlined,
  CloudOutlined,
} from '@ant-design/icons-vue';

import { Icon } from '/@/components/Icon';
import { PageWrapper } from '/@/components/Page';
import { sampleMarkManualCheck, sampleSecondVerify, sampleCdfOut } from '/@/api/sampleQuery';
import SampleLocator from '/@/components/Laboman/SampleLocator/index.vue';
import SampleList from '/@/components/Laboman/SampleList/index.vue';
import PatientInfo from '/@/components/Laboman/PatientInfo/index.vue';
import PatientCheckResult from '/@/components/Laboman/PatientCheckResultUn/index.vue';
import ItemResultGrid from '/@/components/Laboman/ItemResultGridUn/index.vue';
import SampleGraph from '/@/components/Laboman/SampleGraph/index.vue';
import CompareRounds from '/@/components/Laboman/CompareRounds/index.vue';
import HisLog from '/@/components/Laboman/HisLog/index.vue';
import IpMessage from '/@/components/Laboman/IpMessage/index.vue';
import ActionQflag from '/@/components/Laboman/ActionQflag/index.vue';
import NotAcceptList from '/@/components/Laboman/NotAcceptList/index.vue';
import DescriptionEditor from '/@/components/Laboman/PatientInfo/desc_edt.vue';
import SamplePrint from './sample_print.vue';
import { useI18n } from '/@/hooks/web/useI18n';
import { FlowChart } from '/@/components/FlowChart copy';

import { getAiPortOpen, getAiDiagnose, tongYiChat, getAiServiceStart, delAiDiagnose } from '/@/api/ai';

import moment from 'moment';
import { marked } from 'marked'; // 需要安装marked库

const dateFormat = 'YYYY-MM-DD';

export default defineComponent({
  name: 'sample_today',
  components: {
    Icon,
    Button,
    Row,
    Col,
    Tabs,
    TabPane,
    Card,
    Popconfirm,
    PageWrapper,
    Dropdown,
    Menu,
    MenuItem,
    Spin,
    Alert,
    Drawer,
    SampleLocator,
    SampleList,
    PatientInfo,
    PatientCheckResult,
    ItemResultGrid,
    SampleGraph,
    CompareRounds,
    HisLog,
    IpMessage,
    ActionQflag,
    NotAcceptList,
    DescriptionEditor,

    LineChartOutlined,
    AlertOutlined,
    CloudOutlined,
    OrderedListOutlined,
    ArrowUpOutlined,
    ArrowDownOutlined,
    DownOutlined,
    SamplePrint,
    FlowChart,
    Modal,
  },
  setup() {
    const data = reactive({
      tatsample: {},
      current_sample_params: {},
      sample_query_params: {},
      drawerVisible: false,
      componentKey : 1,
    });
    const padding_size = 10;
    const left_col_width = ref(240);
    const middel_col_width = ref(500);
    const right_col_width = ref(500);

    const tabs = ref(null);

    const print_preview_dlg = ref(null);

    const sample_locator = ref(null);
    const sample_list = ref(null);
    const patient_info = ref(null);
    const patient_chk_result = ref(null);
    const item_result_grid = ref(null);
    const sample_graph = ref(null);
    const sample_graph_float = ref(null);
    const compare_rounds = ref(null);
    const his_log = ref(null);
    const ip_message_float = ref(null);
    const action_qflag = ref(null);
    const not_accept_list = ref(null);

    const desc_edt = ref(null);
    const hasSample = ref(false);

    const floatwindow_graph = ref(null);
    const floatwindow_graph_visible = ref(false);
    const floatwindow_ipmsg = ref(null);
    const floatwindow_ipmsg_visible = ref(false);

    const floatwindow_ai = ref(null);
    const floatwindow_ai_visible = ref(false);

    const last_sample_params = ref(null);

    const ai_service_start = ref(false);
    const ai_port_avaliable = ref(null);
    const ai_button_status = ref(null);
    const ai_diagnose_text = ref(null);

    const { t } = useI18n();

    onMounted(() => {
      let query_params = {};

      // 生成默认值
      const today_ = new Date();
      const today = moment(today_);
      query_params = {
        sample_date: today.format(dateFormat),
        instrument: 'XN',
        sample_no: '',
        sample_info: '',
      };

      sample_locator.value.applyFilter(query_params);
      sample_locator.value.handleSubmit();

      checkAiServiceStart();
      checkAiPortOpen();

    });

    const showModal = () => {
      data.componentKey = data.componentKey + 1
      data.drawerVisible = true;
    }

    const onClose = () => {
      data.drawerVisible = false;
    }

    const checkAiServiceStart = async () => {
      await getAiServiceStart().then((res) => {
        ai_service_start.value = res == '1' ? true : false;
      });
    };

    const checkAiPortOpen = async () => {
      await getAiPortOpen().then((res) => {
        ai_port_avaliable.value = res;
        const language = t('general.tab.refresh')
        if (language == 'Refresh'){
          if (res) {
            ai_button_status.value = 'AI diagnosis';
          } else {
            ai_button_status.value = 'AI unavailable';
          }
        }else{
          if (res) {
            ai_button_status.value = 'AI诊断';
          } else {
            ai_button_status.value = 'AI不可用';
          }
        }
          
      });
    };

    const handlerFilterChange = (params) => {
      data.sample_query_params = params;
      sample_list.value.query(data.sample_query_params);

    };

    const update_samples = () => {
      sample_list.value.query(data.current_sample_params);
    };

    const handleRowChange = (value) => {
      let params = {
        sample_date: null,
        instrument: null,
        sample_no: null,
        sample_info: null,
      };

      if (value != null) {
        params = {
          sample_date: value.sample_date,
          instrument: value.instrument,
          sample_no: value.sample_no,
          sample_info: value.sample_info,
        };
      }
      data.current_sample_params = { ...params };
      sample_locator.value.updateSample(params);

      let _hasSample = false;
      if (data.current_sample_params.sample_no != null) {
        _hasSample = true;
      }
      hasSample.value = _hasSample;

      last_sample_params.value = { ...params };
      updateFloatWindow_graph();
      updateFloatWindow_ipmsg();

      patient_info.value.loadData(hasSample.value, params);
      patient_chk_result.value.loadData(hasSample.value, params);
      item_result_grid.value.loadData(hasSample.value, params);

      sample_graph.value.loadData(hasSample.value, params);
      compare_rounds.value.loadData(hasSample.value, params);
      his_log.value.loadData(hasSample.value, params);
      action_qflag.value.loadData(hasSample.value, params);
      not_accept_list.value.loadData(hasSample.value, params);

      getAiDiagnose(params).then((res) => {
        if (res.status == 'error') {
          ai_button_status.value = '诊断标本';
        }else if(res.status == 'pending'){
          ai_button_status.value = '诊断中...';
        }else{
          ai_button_status.value = '查看诊断';
          ai_diagnose_text.value = res.text;
        };
      });
    };
  
    const loadAiDiagnose = async (hasSample, params, recursionCount = 0) => {
      // 添加最大递归深度限制，防止无限递归
      const MAX_RECURSION = 10;
      if (recursionCount > MAX_RECURSION) {
        console.warn('达到最大递归深度，停止查询');
        ai_port_avaliable.value = true;
        ai_diagnose_text.value = '查询超时，请手动刷新';
        return;
      }
      
      ai_diagnose_text.value = '';
      if (hasSample && ai_port_avaliable.value && ai_service_start.value) {

        try {
          const res = await getAiDiagnose(params);
          
          if (res.status == 'error') {
            const tongYiRes = await tongYiChat(params);
            
            // 再次检查当前选中的标本是否与查询的标本一致
            if (data.current_sample_params && 
                (data.current_sample_params.sample_no != params.sample_no ||
                 data.current_sample_params.sample_date != params.sample_date)) {
              // 递归调用时使用当前选中的标本参数，并增加递归计数
              params.sample_no = data.current_sample_params.sample_no;
              params.sample_date = data.current_sample_params.sample_date;

              ai_port_avaliable.value = true;
              console.log('当前选中的标本与查询标本不一致，使用新标本重新查询', params);
              return loadAiDiagnose(true, params, recursionCount + 1);
            }

            ai_port_avaliable.value = true;
            ai_diagnose_text.value = tongYiRes.text;
          } else {
            ai_port_avaliable.value = true;
            ai_diagnose_text.value = res.text;
          }
        } catch (error) {
          console.error('诊断查询出错:', error);
          ai_port_avaliable.value = true;
          ai_diagnose_text.value = '查询诊断时发生错误';
        }
      }
    };


    const _onResize = debounce(() => {
      updateRootDivSize();
    }, 200);

    const onWindowResize = () => {
      _onResize();
    };

    const observer = new ResizeObserver((entries) => {
      _onResize();
    });

    onMounted(() => {
      window.addEventListener('resize', onWindowResize);
      onWindowResize();

      const root_div = document.getElementById('root_div');
      observer.observe(root_div);
    });

    onBeforeUnmount(() => {
      window.removeEventListener('resize', onWindowResize);
      observer.disconnect();
    });

    const updateRootDivSize = () => {
      try {
        const bodyHeight = document.body.clientHeight;

        const header = document.querySelector('div.vben-layout-multiple-header');
        const headerHeight = header.offsetHeight;
        const headerWidth = header.offsetWidth;

        const footer_height = 44;

        const _rootDivHeight = bodyHeight - headerHeight - padding_size;

        const rootDivEle = document.getElementById('root_div');
        rootDivEle.style.height = _rootDivHeight + 'px';

        const rootDivWidth = rootDivEle.offsetWidth;
        const bodyDivWrapEle = document.querySelector('.body_div_wrap');
        const bodyDivWrapWidth = rootDivWidth - 5;
        bodyDivWrapEle.style.width = bodyDivWrapWidth + 'px';

        const _bodyDivHeight = _rootDivHeight - footer_height;
        const bodyDivEle = document.querySelector('.body_div');
        bodyDivEle.style.height = _bodyDivHeight + 'px';
        bodyDivEle.style.width = '9999px';

        const _rightColWidth =
          headerWidth - left_col_width.value - middel_col_width.value - padding_size * 2;
        right_col_width.value = _rightColWidth;

        //
        const tabPane = document.querySelector('div#right_panel div.ant-tabs-top-content');

        let _tabContentHeight =
          bodyHeight -
          headerHeight -
          padding_size -
          tabPane.offsetTop -
          padding_size -
          40 -
          footer_height;

        const bottom_toolbar = 30;
        _tabContentHeight -= bottom_toolbar;

        sample_list.value.updateHeight(_tabContentHeight - 30);
        sample_graph.value.updateHeight(_tabContentHeight);
        compare_rounds.value.updateHeight(_tabContentHeight);
        his_log.value.updateHeight(_tabContentHeight);
        action_qflag.value.updateHeight(_tabContentHeight);
        not_accept_list.value.updateHeight(_tabContentHeight);
      } catch (ex) {}
    };

    const handleManualPass = () => {
      sampleMarkManualCheck(data.current_sample_params, true).then(() => {
        const language = t('general.tab.refresh')
        if (language == 'Refresh'){
          message.success("Tagged 'ManualV'");
        }else{
          message.success("已标记 '人工审核'");
        }      
        update_samples();
      });
    };
    const handleManualNotPass = () => {
      sampleMarkManualCheck(data.current_sample_params, false).then(() => {
        const language = t('general.tab.refresh')
        if (language == 'Refresh'){
          message.success("Tagged 'Manual Interception'");
        }else{
          message.success("已标记 '人工审核'");
        }
        update_samples();
      });
    };

    const handleSecondVerify = () => {
      let text = patient_info.value.patientInfo.description;
      desc_edt.value.showDlg(text);
    };
    const handleDescChanged = (text) => {
      sampleSecondVerify(data.current_sample_params, text).then(() => {
        const language = t('general.tab.refresh')
        if (language == 'Refresh'){
          message.success("Tagged 'Micro'");
        }else{
          message.success("已标记 '镜检审核'");
        }
        update_samples();
      });
    };

    const handleTrustChange = () => {
      update_samples();
    };

    const handleGoPrev = () => {
      sample_list.value.goPrev();
    };

    const handleGoNext = () => {
      sample_list.value.goNext();
    };

    const _handleKeydown = (evt) => {
      if (print_preview_dlg.value.is_visible()) {
        return;
      }

      if (evt.key == 'ArrowDown') {
        handleGoNext();
      } else if (evt.key == 'ArrowUp') {
        handleGoPrev();
      } else if (evt.key == 'F8') {
        handleManualPass();
      } else if (evt.key == 'F9') {
        handleManualNotPass();
      }
    };

    const handleKeydown = debounce((evt) => {
      _handleKeydown(evt);
    }, 100);

    onActivated(() => {
      window.addEventListener('keydown', handleKeydown);
    });

    onDeactivated(() => {
      window.removeEventListener('keydown', handleKeydown);

      floatwindow_graph_visible.value = false;
      floatwindow_ipmsg_visible.value = false;
    });

    const updateFloatWindow_graph = () => {
      if (floatwindow_graph_visible.value) {
        if (sample_graph_float.value) {
          sample_graph_float.value.loadData(hasSample.value, last_sample_params.value);
        }
      }
    };

    const updateFloatWindow_ipmsg = () => {
      if (floatwindow_ipmsg_visible.value) {
        if (ip_message_float.value) {
          ip_message_float.value.loadData(hasSample.value, last_sample_params.value);
        }
      }
    };

    const toggleFloatWindow_graph = () => {
      floatwindow_graph_visible.value = !floatwindow_graph_visible.value;
      nextTick(() => {
        updateFloatWindow_graph();
      });
    };
    const toggleFloatWindow_ipmsg = () => {
      floatwindow_ipmsg_visible.value = !floatwindow_ipmsg_visible.value;
      nextTick(() => {
        updateFloatWindow_ipmsg();
      });
    };

    const toggleFloatWindow_ai = () => {

      let _hasSample = false;
      if (data.current_sample_params.sample_no != null) {
        _hasSample = true;
      }
      hasSample.value = _hasSample;
      loadAiDiagnose(hasSample.value, data.current_sample_params);

      getAiDiagnose(data.current_sample_params).then((res) => {
        if (res.status == 'error' || res.status == 'pending') {
          ai_button_status.value = '诊断中...';
          return;
        }else{
          floatwindow_ai_visible.value = !floatwindow_ai_visible.value;
          nextTick(() => {
            updateFloatWindow_ipmsg();
          });
        };
      });
    };

    const handleFloatWindowShow = () => {
      if (!floatwindow_ipmsg_visible.value) {
        return;
      }
      handleFloatWindowZoom();
    };

    const handleFloatWindowZoom = () => {
      if (!floatwindow_ipmsg.value) {
        return;
      }
      let ele = floatwindow_ipmsg.value.getBox();
      let height = parseInt(ele.style.height.replace('px', ''));
      ip_message_float.value.updateHeight(height - 60);
    };

    const handlePatientInfoSaved = (params) => {
      sample_locator.value.applyFilter(params);
      sample_locator.value.handleSubmit();
    };

    const handlePrintClick = (params) => {
      let key = params.key;

      let print_params = {
        sample_date: data.current_sample_params.sample_date,
        sample_no: data.current_sample_params.sample_no,
      };

      let printable_items = item_result_grid.value.get_printable_items();
      if (key == 'preview') {
        print_preview_dlg.value.doPrint(print_params, printable_items, true);
      }
      if (key == 'print') {
        print_preview_dlg.value.doPrint(print_params, printable_items, false);
      }
    };

    const handleCdfOut = () => {
      let params = {
        sample_date: data.current_sample_params.sample_date,
        sample_no: data.current_sample_params.sample_no,
      };
      sampleCdfOut(params).then(() => {
        const language = t('general.tab.refresh')
        if (language == 'Refresh'){
          message.success('submitted output result');
        }else{
          message.success('已提交生成 输出结果');
        }
        
      });
    };

    const renderMarkdown = (text) => {
      if (!text) return '';
      try {
        // 先将 think 标签部分用特殊标记替换，避免被 markdown 处理
        const thinkBlocks = [];
        let processedText = text.replace(/<think>([\s\S]*?)<\/think>/g, (match, content) => {
          const id = `think-${Math.random().toString(36).substr(2, 9)}`;
          // 存储 think 内容
          thinkBlocks.push({
            id,
            content: content.trim()
          });
          // 使用占位符
          return `\n<!--THINK_BLOCK_${id}-->\n`;
        });

        // 处理主要内容的 markdown
        processedText = marked(processedText);

        // 还原 think 块，并处理其中的 markdown
        processedText = processedText.replace(
          /<!--THINK_BLOCK_(think-[a-z0-9]+)-->/g,
          (match, id) => {
            const block = thinkBlocks.find(b => b.id === id);
            if (!block) return match;
            
            const markedContent = marked(block.content);
            
            return `<div class="think-container">
              <div class="flex justify-between items-center">
                <details class="think-details flex-1" id="${id}">
                  <summary class="think-summary">
                    <span class="think-icon">🤔</span>思考过程
                    <span class="think-status"></span>
                  </summary>
                  <div class="think-content">${markedContent}</div>
                </details>
                <button class="ml-2 px-3 py-1.5 bg-blue-400 text-white rounded-md text-xs font-medium 
                       hover:bg-blue-500 transition-all duration-200 ease-in-out 
                       inline-flex items-center border border-blue-300 hover:border-blue-400" 
                        style="line-height: 1.5;" 
                        onclick="handleRediagnose('${id}')">
                  <svg class="w-3.5 h-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" 
                       style="opacity: 0.9; display: inline-block; vertical-align: middle;">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <span style="vertical-align: middle;">重新诊断</span>
                </button>
              </div>
            </div>`;
          }
        );

        return processedText;
      } catch (e) {
        console.error('Markdown rendering error:', e);
        return text;
      }
    };

    const handleRediagnose = (thinkId) => {
      delAiDiagnose(data.current_sample_params);
      tongYiChat(data.current_sample_params);
      floatwindow_ai_visible.value = false;
    };

    // 确保将函数暴露到全局，因为按钮的 onclick 是在 HTML 字符串中
    window.handleRediagnose = handleRediagnose;

    return {
      data,
      left_col_width,
      middel_col_width,
      right_col_width,
      tabs,
      print_preview_dlg,
      sample_locator,
      handlerFilterChange,
      sample_list,
      handleRowChange,
      patient_info,
      patient_chk_result,
      item_result_grid,
      sample_graph,
      sample_graph_float,
      compare_rounds,
      his_log,
      //ip_message,
      ip_message_float,
      action_qflag,
      not_accept_list,

      handleManualPass,
      handleManualNotPass,
      handleSecondVerify,
      desc_edt,
      handleDescChanged,

      handleTrustChange,

      hasSample,

      floatwindow_ipmsg,
      floatwindow_ipmsg_visible,
      floatwindow_graph,
      floatwindow_graph_visible,

      toggleFloatWindow_graph,
      toggleFloatWindow_ipmsg,

      floatwindow_ai,
      floatwindow_ai_visible,
      toggleFloatWindow_ai,
      ai_port_avaliable,
      ai_button_status,
      loadAiDiagnose,
      ai_diagnose_text,
      checkAiServiceStart,
      ai_service_start,

      handleFloatWindowShow,
      handleFloatWindowZoom,

      handleGoPrev,
      handleGoNext,

      handlePatientInfoSaved,

      handlePrintClick,

      handleCdfOut,
      showModal,
      t,
      imageStyle: { position: 'absolute', top: '80%', left: '92%', zIndex: 10000, },
      onClose,
      renderMarkdown,
    };
  },
});
</script>
<style scoped lang="less">
@padding_size: 10px;

#root_div {
  padding-top: @padding_size;
  //overflow: hidden;
}
.vertical_panel {
  float: left;
  height: 100%;
  overflow: hidden;
}
.with_padding_left {
  padding-left: @padding_size;
}
.footer_div {
  padding: 5px;
  height: 1%;
  text-align: center;
}
.bottom_buttons {
  width: auto;
}

.bubble-button-box {
  position: relative;
  width: 200px;
  height: 50px;
  margin: 5px;
}
 
.bubble-button {
  position: relative; 
  background-color: #f0f0f0; 
  border-radius: 10px; 
  padding: 0px 20px; 
  color: #333; 
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.drawer {
  width: 50%; /* 抽屉宽度 */
  height: 100%;
}
/* 抽屉打开时的样式 */
.drawer-open {
  transform: translateX(50%);
  width: 50%;
}

.drawers{
  width: 50%;
}

.model {
  width: 50%;
  position: absolute;
}

.bubble-image { 
  position: relative; 
  width: 80px;
  height: 80px;
  overflow: hidden;
  display: block; 
  border-radius: 15px; 
  mix-blend-mode: multiply;
  //opacity: 0.9;
  position: 'absolute';
}

.markdown-content {
  padding: 10px;
  overflow-y: auto;
  max-height: 100%;
  line-height: 1.3; // 修改为合理的行高
}

.markdown-content :deep(h1) {
  font-size: 1.6em;
  margin: 0.5em 0 0.3em 0; // 调整上下边距
}

.markdown-content :deep(h2) {
  font-size: 1.4em;
  margin: 0.4em 0 0.2em 0;
}

.markdown-content :deep(h3) {
  font-size: 1.2em;
  margin: 0.3em 0 0.2em 0;
}

.markdown-content :deep(p) {
  margin: 0.3em 0; // 调整段落间距
  line-height: 1.4; // 段落内行高
}

.markdown-content :deep(ul), .markdown-content :deep(ol) {
  padding-left: 1.5em; // 减少缩进
  margin: 0.2em 0;
}

.markdown-content :deep(li) {
  margin: 0.1em 0; // 添加列表项间距
}

.markdown-content :deep(code) {
  background-color: #f5f5f5;
  padding: 0.1em 0.3em; // 减少内边距
  border-radius: 3px;
  font-family: monospace;
}

.markdown-content :deep(pre) {
  background-color: #f5f5f5;
  padding: 0.6em; // 减少内边距
  border-radius: 5px;
  overflow-x: auto;
  margin: 0.4em 0;
}

.markdown-content :deep(blockquote) {
  border-left: 3px solid #ddd; // 减小边框
  padding-left: 0.8em;
  color: #666;
  margin: 0.3em 0;
}

.markdown-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 0.4em 0;
  font-size: 0.95em; // 稍微减小表格字体
}

.markdown-content :deep(th), .markdown-content :deep(td) {
  border: 1px solid #ddd;
  padding: 4px 6px; // 减少单元格内边距
  text-align: left;
}

.markdown-content :deep(th) {
  background-color: #f2f2f2;
}

:deep(.think-container) {
  margin: 16px 0;

  .think-details {
    border: 1px solid #e8e8e8;
    border-radius: 6px;
    background: #fafafa;
    transition: all 0.3s;

    &[open] {
      background: #f0f5ff;
      border-color: #d6e4ff;

      .think-summary {
        margin-bottom: 8px;
        border-bottom: 1px dashed #d6e4ff;
      }

      .think-status::after {
        content: '(已展开)';
        color: #1890ff;
      }
    }

    .think-summary {
      padding: 12px 16px;
      cursor: pointer;
      user-select: none;
      list-style: none !important; // 强制移除列表样式
      font-weight: 500;
      display: flex;
      align-items: center;
      gap: 8px;

      &::marker,
      &::-webkit-details-marker {
        display: none !important; // 强制隐藏默认标记
      }

      &:hover {
        background: #f0f5ff;
      }
    }

    .think-icon {
      font-size: 16px;
      line-height: 1;
    }

    .think-content {
      padding: 16px;
      background: #fff;
      border-radius: 0 0 6px 6px;
      line-height: 1.6;

      // 确保内容中的 markdown 样式正确
      :deep(p) {
        margin: 0.5em 0;
      }

      :deep(ul), :deep(ol) {
        margin: 0.5em 0;
        padding-left: 2em;
      }
    }
  }
}

// 确保 details 元素默认是折叠的
:deep(details:not([open])) {
  .think-content {
    display: none;
  }
}
</style>
