# 使用虚拟用户进行自动化 K6 负载测试

此代码库包含两个组件：

1. **K7 负载测试自动化**  
    这个基于 Python 的系统幽默地命名为 **K7**，用于自动化执行 K6 脚本。K7 不仅仅是简单地增加负载，它还能确定每秒钟每个端点可以承受的**稳定虚拟用户（VUs）最大值**，而不会导致性能崩溃。这使得快速高效地识别系统的瓶颈成为可能。
2. **K6 测试脚本**  
    [K6](https://k6.io/) 是 Grafana 提供的开源负载测试工具。本测试脚本模拟多个虚拟用户（VUs），逐步增加负载并根据定义的性能阈值评估系统性能。

K6 提供核心负载测试功能，而 K7 增加了高级的编排和自动化，使测试过程更加高效和精准。

---
## 目录
1. [概述](#%E6%A6%82%E8%BF%B0)
2. [测试脚本](#%E6%B5%8B%E8%AF%95%E8%84%9A%E6%9C%AC)
3. [配置选项](#%E9%85%8D%E7%BD%AE%E9%80%89%E9%A1%B9)
4. [身份验证设置（可选）](#%E8%BA%AB%E4%BB%BD%E9%AA%8C%E8%AF%81%E8%AE%BE%E7%BD%AE%E5%8F%AF%E9%80%89)
5. [运行测试](#%E8%BF%90%E8%A1%8C%E6%B5%8B%E8%AF%95)
6. [阈值和验证](#%E9%98%88%E5%80%BC%E5%92%8C%E9%AA%8C%E8%AF%81)
7. [支持的端点](#%E6%94%AF%E6%8C%81%E7%9A%84%E7%AB%AF%E7%82%B9)

---
## 概述
系统运行 K6 负载测试包含两个主要阶段：
1. **逐步增加阶段**：逐步增加虚拟用户数量。
2. **即时负载阶段**：保持稳定的虚拟用户负载。

测试会验证性能阈值是否达标，并确保系统可以在不出现问题的情况下处理指定负载。
此外，**K7 Python 脚本**可用于灵活地管理和执行测试，支持详细日志（`-v`/`--verbose`）和帮助（`-h`/`--help`）标志。

---
### 命令行参数
该脚本支持以下选项来配置测试：
- **`-h` / `--help`**：返回所有配置选项的列表。
- **`-vu` / `--initial_vus`**：设置初始虚拟用户数量。较低的值适用于测试立即失败的情况。
- **`-i` / `--increment`**：设置虚拟用户的增加量。较小的增量提高准确性，但需要更长时间确定稳定的虚拟用户数量（建议：100）。
- **`-vr` / `--validation_runs`**：设置验证运行次数。默认值为 4。
- **`-d` / `--delay_between_tests`**：设置测试之间的延迟时间（秒）。默认值为 10 秒。
- **`-t` / `--duration`**：设置 K6 测试时长（秒）。默认值为 60 秒。
- **`-rt` / `--rampup_time`**：设置逐步增加阶段的时间（秒）。默认值为 15 秒。
- **`-v` / `--verbose`**：启用详细输出，显示 K6 日志。
- **`--k6_script`**：指定 K6 测试脚本的路径。请参考模板了解结构。

### 运行命令
可以通过以下方式运行脚本并传入所有参数：
```bash
python k7.py -vu 100 -i 50 -vr 5 -d 5 -t 60 -rt 30 -v --k6_script test-script.js
```

示例说明：
- 初始虚拟用户数为 100（`-vu 100`）
- 每次增加 50 虚拟用户（`-i 50`）
- 验证运行次数为 5 次（`-vr 5`）
- 测试间隔 15 秒（`-d 5`）
- 测试时长为 60 秒（`-t 60`）
- 逐步增加阶段时长为 30 秒（`-rt 30`）
- 启用详细输出（`-v`）
- 使用 `test-script.js` 作为 K6 测试脚本（`--k6_script test-script.js`）。

---
## 测试脚本
主测试脚本（`test-script.js`）模拟虚拟用户（VUs）发起 HTTP GET 请求。脚本结构包含两个加载阶段，通过 K6 的 `ramping-vus` 和 `constant-vus` 执行器管理虚拟用户数量的增长。  
只需修改此脚本中的**端点**，以及（可选）需要身份验证或其他初始化步骤时的 **setup** 函数。

示例脚本如下：
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

// 配置虚拟用户数量、逐步增加时间和测试时长
const target = __ENV.VUS || 300;
const rampupTime = __ENV.RAMPUP || "5s";
const duration = __ENV.DURATION || "1m";

export const options = {
  scenarios: {
    rampUp: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [{ duration: rampupTime, target: target }],
      tags: { rampUp: 'true' },
    },
    instantLoad: {
      executor: 'constant-vus',
      vus: target,
      duration: duration,
      startTime: rampupTime,
      tags: { rampUp: 'false' },
    },
  },
  thresholds: {
    'http_req_failed{rampUp:false}': [{ threshold: 'rate==0', abortOnFail: true }],
    'http_req_duration{rampUp:false}': [{ threshold: 'p(95)<1000', abortOnFail: true }],
  },
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)'],
};

// 每个虚拟用户执行的主函数
export default function () {
  http.get('http://localhost:3000/channel');
  http.get('http://localhost:3000/channel/create');
  sleep(1); // 模拟请求间的等待时间
}
```

---
## 身份验证设置（可选）
如果测试需要 JWT 身份验证，可以设置登录流程如下：
```javascript
export function setup() {
  const loginHeaders = { 'Content-Type': 'application/json' };

  const loginResponse = http.post('http://localhost/auth/login', JSON.stringify({
    name: 'your_username',
    password: 'your_password',
  }), { headers: loginHeaders });

  const isLoginSuccessful = check(loginResponse, {
    'login successful': (res) => res.status === 200 && res.json('accessToken') !== undefined,
  });

  if (!isLoginSuccessful) {
    throw new Error('Login failed');
  }

  return loginResponse.json('accessToken');
}

export default function (accessToken) {
  const authHeaders = { Authorization: `Bearer ${accessToken}` };

  http.get('http://localhost:3000/channel', { headers: authHeaders });
  http.get('http://localhost:3000/channel/create', { headers: authHeaders });
  sleep(1);
}
```

---
## 阈值和验证
以下性能阈值用于验证：
- **HTTP 请求失败率**：失败率应为 0%（`rate==0`）。
- **HTTP 请求时长**：95% 的请求应在 1000 毫秒内完成（`p(95)<1000`）。
如果超出阈值，测试将自动终止。

---

## 支持的端点
K6 支持所有 HTTP 方法（不支持 trace 方法）。有关详细信息，请访问 [K6 文档](https://k6.io/)。