# 智能旅游规划Agent

基于非遗文化的智能旅游规划服务，集成阿里云大模型和多种API服务，为用户提供个性化的文化旅游体验。

## 项目概述

本项目是一个智能旅游规划系统，专注于非物质文化遗产的文化旅游体验。系统通过AI技术分析用户需求，结合天气、地理位置等信息，生成个性化的旅游规划方案。

### 核心功能

- 🎯 **智能规划**: 基于AI大模型的旅游路线规划
- 🏛️ **非遗文化**: 专注非物质文化遗产景点推荐
- 🌤️ **天气集成**: 实时天气信息与出行建议
- 📍 **地理服务**: 百度地图API集成，精准位置服务
- 📊 **进度跟踪**: 实时规划进度监控
- 📱 **前端界面**: 现代化Web界面，支持进度条和结果展示

## 技术架构

### 后端架构

```
Agent/
├── api/                    # FastAPI接口层
│   └── app.py             # 主应用入口
├── core/                   # 核心业务逻辑
│   ├── heritage_analyzer.py   # 非遗项目分析
│   ├── travel_planner.py      # 旅游规划核心
│   └── weather_service.py     # 天气服务
├── models/                 # AI模型集成
│   └── ali_model.py       # 阿里云模型调用
├── utils/                  # 工具模块
│   ├── config.py          # 配置管理
│   └── logger_config.py   # 日志配置
├── data/                   # 数据文件
│   └── heritage_data.json # 非遗项目数据
└── main.py                # 主入口文件
```

### 前端架构

```
frontend/
├── css/                   # 样式文件
│   └── agent/
│       └── travel-planning.css
├── js/                    # JavaScript文件
│   └── agent/
│       └── travel-planning.js
└── index.html            # 主页面
```

## 快速开始

### 环境要求

- Python 3.8+
- Node.js (可选，用于前端开发)

### 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt
```

### 配置API密钥

1. 复制配置文件模板：
```bash
cp utils/config.py.example utils/config.py
```

2. 编辑 `utils/config.py`，填入你的API密钥：
```python
# 阿里云API配置
DASHSCOPE_API_KEY = "your_dashscope_api_key"

# 百度地图API配置
BAIDU_MAP_AK = "your_baidu_map_ak"

# 天气API配置（可选）
WEATHER_API_KEY = "your_weather_api_key"
```

### 启动服务

```bash
# 启动后端API服务
python -m uvicorn api.app:app --host 0.0.0.0 --port 8001 --reload
python manage.py runserver 0.0.0.0:8000
# 或者直接运行
python api/app.py
```

服务启动后，访问：
- API文档: http://localhost:8001/docs
- 健康检查: http://localhost:8001/health
- 前端界面: 打开 `frontend/index.html`

## API文档

### 核心接口

#### 1. 健康检查
```http
GET /health
```

响应示例：
```json
{
  "status": "healthy",
  "timestamp": "2025-08-31T21:42:01.676494",
  "components": {
    "agent": "ok",
    "planner": "ok",
    "api": "ok"
  }
}
```

#### 2. 创建旅游规划
```http
POST /api/travel-plan/create
```

请求体：
```json
{
  "heritage_ids": [1, 2, 3],
  "user_id": "test_user_001",
  "travel_days": 3,
  "departure_location": "西安市",
  "travel_mode": "自驾",
  "budget_range": "中等",
  "group_size": 2,
  "special_requirements": ["文化体验", "美食推荐"],
  "contact_info": {
    "phone": "13800138000",
    "email": "test@example.com"
  }
}
```

响应示例：
```json
{
  "success": true,
  "plan_id": "plan_4623b1a0_20250831_214244",
  "message": "旅游规划任务已启动，请使用plan_id查询进度",
  "data": {
    "plan_id": "plan_4623b1a0_20250831_214244",
    "estimated_time": "2-5分钟",
    "heritage_count": 3,
    "travel_days": 3
  }
}
```

#### 3. 查询规划进度
```http
GET /api/travel-plan/progress/{plan_id}
```

响应示例：
```json
{
  "plan_id": "plan_4623b1a0_20250831_214244",
  "status": "processing",
  "progress": 60,
  "current_step": "生成AI建议",
  "steps": [
    "分析非遗项目",
    "获取天气信息",
    "生成AI建议",
    "优化路线规划",
    "生成完整方案",
    "完成规划"
  ],
  "start_time": "2025-08-31T21:42:44.123456"
}
```

#### 4. 获取规划结果
```http
GET /api/travel-plan/result/{plan_id}
```

响应示例：
```json
{
  "success": true,
  "plan_id": "plan_4623b1a0_20250831_214244",
  "message": "规划获取成功",
  "data": {
    "title": "西安非遗文化3日游",
    "total_days": 3,
    "itinerary": [
      {
        "day": 1,
        "items": [
          {
            "name": "兵马俑",
            "type": "景点",
            "time": "09:00-12:00",
            "description": "世界文化遗产，秦始皇陵兵马俑"
          }
        ]
      }
    ]
  }
}
```

#### 5. 获取规划列表
```http
GET /api/travel-plan/list
```

## 前端集成

### JavaScript SDK

项目提供了完整的前端JavaScript SDK，位于 `frontend/js/agent/travel-planning.js`。

#### 基本使用

```javascript
// 初始化Agent
const agent = new TravelPlanningAgent();

// 创建规划
const planData = {
    heritage_ids: [1, 2, 3],
    travel_days: 3,
    departure_location: "西安市",
    // ... 其他参数
};

agent.createTravelPlan(planData);
```

#### 进度监控

SDK自动处理进度监控，并提供回调函数：

```javascript
// 监听进度更新
agent.onProgressUpdate = (progressData) => {
    console.log(`进度: ${progressData.progress}%`);
    console.log(`当前步骤: ${progressData.current_step}`);
};

// 监听完成事件
agent.onPlanningCompleted = (result) => {
    console.log('规划完成:', result);
};
```

## 开发指南

### 添加新的非遗项目

编辑 `data/heritage_data.json` 文件：

```json
{
  "heritage_items": [
    {
      "id": 4,
      "name": "新的非遗项目",
      "category": "传统技艺",
      "location": "城市名",
      "description": "项目描述",
      "coordinates": {
        "latitude": 34.2619,
        "longitude": 108.9419
      }
    }
  ]
}
```

### 扩展AI模型

在 `models/` 目录下添加新的模型文件：

```python
# models/new_model.py
class NewModel:
    def __init__(self):
        # 初始化模型
        pass
    
    async def generate_suggestion(self, prompt: str) -> str:
        # 实现模型调用逻辑
        pass
```

### 添加新的API接口

在 `api/app.py` 中添加新的路由：

```python
@app.get("/api/new-endpoint")
async def new_endpoint():
    """
    新的API接口
    """
    return {"message": "Hello from new endpoint"}
```

## 测试

### 运行测试

```bash
# 运行API测试



```

### 测试覆盖

项目包含以下测试：

- API接口测试
- 核心功能测试
- 模型集成测试
- 前端功能测试

## 部署

### Docker部署

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8001

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8001"]
```

```bash
# 构建和运行
docker build -t travel-agent .
docker run -p 8001:8001 travel-agent
```

### 生产环境配置

1. 设置环境变量：
```bash
export DASHSCOPE_API_KEY="your_production_key"
export BAIDU_MAP_AK="your_production_key"
```

2. 使用生产级WSGI服务器：
```bash
gunicorn api.app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001
```

## 故障排除

### 常见问题

1. **API密钥错误**
   - 检查 `utils/config.py` 中的密钥配置
   - 确保密钥有效且有足够的配额

2. **模块导入错误**
   - 检查Python路径设置
   - 确保所有依赖已正确安装

3. **进度查询404错误**
   - 确保规划ID正确
   - 检查后台任务是否正常启动

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log
```

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目维护者: [Your Name]
- 邮箱: [your.email@example.com]
- 项目链接: [https://github.com/yourusername/travel-agent]

## 更新日志

### v1.0.0 (2025-08-31)

- ✅ 完成基础架构搭建
- ✅ 集成阿里云大模型
- ✅ 实现非遗项目分析
- ✅ 添加天气服务集成
- ✅ 完成API接口开发
- ✅ 实现前端进度条和结果展示
- ✅ 添加完整的测试覆盖

---

**感谢使用智能旅游规划Agent！** 🎉