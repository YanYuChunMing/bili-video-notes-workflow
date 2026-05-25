import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { Save, Eye, EyeOff, CheckCircle, XCircle, Settings } from 'lucide-react';
import Card from '../components/Card';
import Button from '../components/Button';
import Badge from '../components/Badge';
import Header from '../components/Header';
import Spinner from '../components/Spinner';
import { getConfig, updateConfig, checkApiKey } from '../services/configService';
import type { AppConfig } from '../types/api';

function ToggleSwitch({ enabled, onChange }: { enabled: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!enabled)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 ${
        enabled ? 'bg-primary' : 'bg-gray-200'
      }`}
    >
      <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
        enabled ? 'translate-x-6' : 'translate-x-1'
      }`} />
    </button>
  );
}

type ApiKeyStatus = 'idle' | 'valid' | 'invalid';

export default function SettingsPage() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [formDirty, setFormDirty] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);
  const [checkingApiKey, setCheckingApiKey] = useState(false);
  const [apiKeyStatus, setApiKeyStatus] = useState<ApiKeyStatus>('idle');
  const [apiKeyMessage, setApiKeyMessage] = useState('');

  const [whisperModel, setWhisperModel] = useState('');
  const [whisperLanguage, setWhisperLanguage] = useState('');
  const [whisperDevice, setWhisperDevice] = useState('');
  const [whisperComputeType, setWhisperComputeType] = useState('');

  const [deepseekApiKey, setDeepseekApiKey] = useState('');
  const [deepseekBaseUrl, setDeepseekBaseUrl] = useState('');
  const [deepseekModel, setDeepseekModel] = useState('');

  const [screenshotEnabled, setScreenshotEnabled] = useState(false);
  const [screenshotStrategy, setScreenshotStrategy] = useState('');
  const [screenshotInterval, setScreenshotInterval] = useState(0);
  const [screenshotMaxPerMinute, setScreenshotMaxPerMinute] = useState(0);
  const [screenshotThreshold, setScreenshotThreshold] = useState(0.5);

  useEffect(() => {
    loadConfig();
  }, []);

  async function loadConfig() {
    try {
      setLoading(true);
      const res = await getConfig();
      const cfg = res.data;
      setConfig(cfg);

      setWhisperModel(cfg.whisper.model);
      setWhisperLanguage(cfg.whisper.language);
      setWhisperDevice(cfg.whisper.device);
      setWhisperComputeType(cfg.whisper.compute_type);

      setDeepseekApiKey('');
      setDeepseekBaseUrl(cfg.deepseek.base_url);
      setDeepseekModel(cfg.deepseek.model);

      setScreenshotEnabled(cfg.screenshot.enabled);
      setScreenshotStrategy(cfg.screenshot.strategy);
      setScreenshotInterval(cfg.screenshot.min_interval_seconds);
      setScreenshotMaxPerMinute(cfg.screenshot.max_avg_per_minute);
      setScreenshotThreshold(cfg.screenshot.difference_threshold);

      setFormDirty(false);
    } catch {
      toast.error('加载配置失败');
    } finally {
      setLoading(false);
    }
  }

  function markDirty() {
    setFormDirty(true);
  }

  async function handleSave() {
    try {
      setSaving(true);
      await updateConfig({
        whisper_model: whisperModel,
        whisper_language: whisperLanguage,
        whisper_device: whisperDevice,
        whisper_compute_type: whisperComputeType,
        deepseek_model: deepseekModel,
        deepseek_base_url: deepseekBaseUrl,
        deepseek_api_key: deepseekApiKey || undefined,
        screenshot_enabled: screenshotEnabled,
        screenshot_strategy: screenshotStrategy,
        screenshot_min_interval_seconds: screenshotInterval,
        screenshot_max_avg_per_minute: screenshotMaxPerMinute,
        screenshot_difference_threshold: screenshotThreshold,
      });
      toast.success('配置已保存');
      setFormDirty(false);
    } catch {
      toast.error('保存配置失败');
    } finally {
      setSaving(false);
    }
  }

  async function handleCheckApiKey() {
    try {
      setCheckingApiKey(true);
      setApiKeyStatus('idle');
      setApiKeyMessage('');
      const res = await checkApiKey();
      if (res.data.valid) {
        setApiKeyStatus('valid');
        setApiKeyMessage(res.data.message);
        toast.success('API Key 有效');
      } else {
        setApiKeyStatus('invalid');
        setApiKeyMessage(res.data.message);
        toast.error('API Key 无效');
      }
    } catch {
      setApiKeyStatus('invalid');
      setApiKeyMessage('验证请求失败');
      toast.error('验证请求失败');
    } finally {
      setCheckingApiKey(false);
    }
  }

  if (loading) {
    return (
      <div>
        <Header title="系统设置" subtitle="管理应用全局配置" />
        <Spinner className="min-h-[400px]" />
      </div>
    );
  }

  return (
    <div>
      <Header
        title="系统设置"
        subtitle="管理应用全局配置"
        action={
          <Button
            variant={formDirty ? 'primary' : 'secondary'}
            onClick={handleSave}
            loading={saving}
            disabled={!formDirty}
          >
            <Save size={16} />
            保存
          </Button>
        }
      />

      <div className="space-y-6">

        <Card>
          <div className="flex items-center gap-2 mb-5">
            <Settings size={20} className="text-primary" />
            <h2 className="text-lg font-semibold text-text">Whisper 设置</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-text mb-1.5">模型</label>
              <select
                value={whisperModel}
                onChange={(e) => { setWhisperModel(e.target.value); markDirty(); }}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-text bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              >
                <option value="tiny">tiny</option>
                <option value="base">base</option>
                <option value="small">small</option>
                <option value="medium">medium</option>
                <option value="large">large</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-text mb-1.5">语言</label>
              <input
                type="text"
                value={whisperLanguage}
                onChange={(e) => { setWhisperLanguage(e.target.value); markDirty(); }}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-text bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                placeholder="zh"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text mb-1.5">设备</label>
              <select
                value={whisperDevice}
                onChange={(e) => { setWhisperDevice(e.target.value); markDirty(); }}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-text bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              >
                <option value="cuda">cuda</option>
                <option value="cpu">cpu</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-text mb-1.5">计算精度</label>
              <select
                value={whisperComputeType}
                onChange={(e) => { setWhisperComputeType(e.target.value); markDirty(); }}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-text bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              >
                <option value="auto">auto</option>
                <option value="float16">float16</option>
                <option value="int8">int8</option>
              </select>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-2 mb-5">
            <Settings size={20} className="text-primary" />
            <h2 className="text-lg font-semibold text-text">DeepSeek 设置</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-text mb-1.5">API Key</label>
              <div className="relative">
                <input
                  type={showApiKey ? 'text' : 'password'}
                  value={deepseekApiKey}
                  onChange={(e) => { setDeepseekApiKey(e.target.value); markDirty(); setApiKeyStatus('idle'); }}
                  className="w-full rounded-lg border border-gray-200 px-3 py-2 pr-10 text-sm text-text bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  placeholder="sk-..."
                />
                <button
                  type="button"
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-text-secondary hover:text-text"
                >
                  {showApiKey ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-text mb-1.5">Base URL</label>
              <input
                type="text"
                value={deepseekBaseUrl}
                onChange={(e) => { setDeepseekBaseUrl(e.target.value); markDirty(); }}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-text bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                placeholder="https://api.deepseek.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text mb-1.5">模型名称</label>
              <input
                type="text"
                value={deepseekModel}
                onChange={(e) => { setDeepseekModel(e.target.value); markDirty(); }}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-text bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                placeholder="deepseek-chat"
              />
            </div>
            <div className="flex items-end">
              <div className="flex items-center gap-3">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleCheckApiKey}
                  loading={checkingApiKey}
                >
                  验证 API Key
                </Button>
                {apiKeyStatus === 'valid' && (
                  <Badge variant="success">
                    <CheckCircle size={12} className="mr-1" />
                    有效
                  </Badge>
                )}
                {apiKeyStatus === 'invalid' && (
                  <Badge variant="error">
                    <XCircle size={12} className="mr-1" />
                    {apiKeyMessage || '无效'}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-2 mb-5">
            <Settings size={20} className="text-primary" />
            <h2 className="text-lg font-semibold text-text">截图设置</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-text">启用截图</label>
              <ToggleSwitch
                enabled={screenshotEnabled}
                onChange={(v) => { setScreenshotEnabled(v); markDirty(); }}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text mb-1.5">策略</label>
              <select
                value={screenshotStrategy}
                onChange={(e) => { setScreenshotStrategy(e.target.value); markDirty(); }}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-text bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              >
                <option value="learning">learning</option>
                <option value="visual_change">visual_change</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-text mb-1.5">截图间隔（秒）</label>
              <input
                type="number"
                value={screenshotInterval}
                onChange={(e) => { setScreenshotInterval(Number(e.target.value)); markDirty(); }}
                min={1}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-text bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text mb-1.5">每分钟最大截图数</label>
              <input
                type="number"
                value={screenshotMaxPerMinute}
                onChange={(e) => { setScreenshotMaxPerMinute(Number(e.target.value)); markDirty(); }}
                min={1}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-text bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-text mb-1.5">
                相似度阈值：{screenshotThreshold.toFixed(2)}
              </label>
              <input
                type="range"
                min={0.5}
                max={1.0}
                step={0.01}
                value={screenshotThreshold}
                onChange={(e) => { setScreenshotThreshold(Number(e.target.value)); markDirty(); }}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary"
              />
              <div className="flex justify-between text-xs text-text-secondary mt-1">
                <span>0.5</span>
                <span>1.0</span>
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-2 mb-5">
            <Settings size={20} className="text-primary" />
            <h2 className="text-lg font-semibold text-text">项目设置</h2>
          </div>
          {config && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">项目名称</label>
                <p className="text-sm text-text">{config.project.name}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">输出目录</label>
                <p className="text-sm text-text truncate">{config.project.output_dir}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">日志目录</label>
                <p className="text-sm text-text truncate">{config.project.log_dir}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">临时目录</label>
                <p className="text-sm text-text truncate">{config.project.temp_dir}</p>
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-text-secondary mb-1">下载目录</label>
                <p className="text-sm text-text truncate">{config.project.download_dir}</p>
              </div>
            </div>
          )}
        </Card>

      </div>
    </div>
  );
}
