# -*- coding: utf-8 -*-
"""
知识图谱工具集
封装知识图谱的查询能力，供 Agent 调用
"""

from typing import Dict, Any
from loguru import logger

from Agent.tools.base import BaseTool, require_knowledge_graph, resolve_heritage_id


class NearbyHeritageTool(BaseTool):
    """查询邻近非遗项目工具"""
    
    @property
    def name(self) -> str:
        return "nearby_heritage_query"
    
    @property
    def description(self) -> str:
        return """查询指定非遗项目邻近的其他非遗项目。
【功能说明】
基于 Neo4j 知识图谱的地理位置关系（NEAR 边类型），使用 Haversine 公式计算项目间的实际地理距离，
返回距离最近的可顺访非遗项目，帮助用户丰富旅行路线。

【数据结构】
知识图谱存储结构：
- 节点类型：Heritage（非遗项目），包含 id、name、region、latitude、longitude、category、level 等属性
- 边类型：NEAR（邻近关系），通过地理位置计算动态建立
- 查询机制：Cypher 查询 MATCH (h:Heritage {id: $id})-[r:NEAR]-(other:Heritage) RETURN other, r.distance

【应用场景】
1. 用户请求添加项目时：推荐邻近的非遗项目作为顺访选择
2. 路线规划阶段：为已有行程推荐顺路可参观的项目
3. 发现更多非遗：基于已选项目发现周边同类型文化遗产

【使用示例】
用户："我已选择户县农民画，附近还有什么值得去的？"
调用：nearby_heritage_query(heritage_id=17, limit=5)
返回：3-5个距离户县最近的非遗项目，包含距离信息和顺访建议"""
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "heritage_id": {
                    "type": "integer",
                    "description": "非遗项目ID"
                },
                "heritage_name": {
                    "type": "string",
                    "description": "非遗项目名称（可选，与heritage_id二选一）"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量限制，默认5",
                    "default": 5
                }
            },
            "required": []
        }
    
    @require_knowledge_graph
    async def execute(self, kg, **kwargs) -> Dict[str, Any]:
        heritage_id = kwargs.get('heritage_id')
        heritage_name = kwargs.get('heritage_name')
        limit = kwargs.get('limit', 5)
        
        heritage_id = resolve_heritage_id(kg, heritage_id, heritage_name)
        
        if not heritage_id:
            return {
                "success": False,
                "error": "请提供heritage_id或heritage_name"
            }
        
        try:
            nearby = kg.query_nearby_heritages_by_id(heritage_id, limit=limit)
            
            return {
                "success": True,
                "heritage_id": heritage_id,
                "nearby_heritages": nearby,
                "count": len(nearby),
                "hint": f"发现{len(nearby)}个邻近非遗项目，可考虑顺访" if nearby else "暂无邻近项目"
            }
        except Exception as e:
            logger.error(f"查询邻近非遗失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class RelatedHeritageTool(BaseTool):
    """查询相关非遗项目工具"""
    
    @property
    def name(self) -> str:
        return "related_heritage_query"
    
    @property
    def description(self) -> str:
        return """查询与指定非遗项目相关的其他非遗项目。
【功能说明】
基于 Neo4j 知识图谱的多重关系网络，包括类别归属（BELONGS_TO）、地区位置（LOCATED_AT）、
级别认证（HAS_LEVEL）等关系类型，智能发现与目标项目相关的其他非遗项目。

【数据结构】
知识图谱存储结构：
- 节点类型：
  * Heritage：非遗项目（id, name, category, region, level, description）
  * Category：类别节点（传统音乐、传统舞蹈、传统技艺等）
  * Region：地区节点（西安市、宝鸡市、咸阳市等）
  * Level：级别节点（国家级、省级、市级）
- 边类型：
  * BELONGS_TO：项目 → 类别
  * LOCATED_AT：项目 → 地区
  * HAS_LEVEL：项目 → 级别
- 查询机制：
  * 同类查询：MATCH (h:Heritage {id: $id})-[:BELONGS_TO]->(c:Category)<-[:BELONGS_TO]-(other:Heritage)
  * 同地区查询：MATCH (h:Heritage {id: $id})-[:LOCATED_AT]->(r:Region)<-[:LOCATED_AT]-(other:Heritage)

【应用场景】
1. 用户请求添加项目时：推荐同类别的其他非遗项目，丰富文化体验
2. 主题旅行规划：为某类非遗主题（如"传统技艺"）推荐相关项目
3. 文化深度探索：基于已有项目推荐同地区或同级别的其他项目

【使用示例】
用户："我喜欢凤翔木版年画，还有什么类似的传统技艺？"
调用：related_heritage_query(heritage_id=20, relation_type="category", limit=5)
返回：5个与凤翔木版年画同类别的传统技艺项目"""
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "heritage_id": {
                    "type": "integer",
                    "description": "非遗项目ID"
                },
                "heritage_name": {
                    "type": "string",
                    "description": "非遗项目名称（可选）"
                },
                "relation_type": {
                    "type": "string",
                    "description": "关系类型：category(同类)、region(同地区)、all(全部)",
                    "default": "all"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量限制，默认5",
                    "default": 5
                }
            },
            "required": []
        }
    
    @require_knowledge_graph
    async def execute(self, kg, **kwargs) -> Dict[str, Any]:
        heritage_id = kwargs.get('heritage_id')
        heritage_name = kwargs.get('heritage_name')
        relation_type = kwargs.get('relation_type', 'all')
        limit = kwargs.get('limit', 5)
        
        heritage_id = resolve_heritage_id(kg, heritage_id, heritage_name)
        
        if not heritage_id:
            return {
                "success": False,
                "error": "请提供heritage_id或heritage_name"
            }
        
        try:
            related = kg.query_related_heritage(heritage_id, relation_type=relation_type, limit=limit)
            
            return {
                "success": True,
                "heritage_id": heritage_id,
                "related_heritages": related,
                "relation_type": relation_type,
                "count": len(related),
                "hint": f"发现{len(related)}个相关非遗项目" if related else "暂无相关项目"
            }
        except Exception as e:
            logger.error(f"查询相关非遗失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class NearbyRegionTool(BaseTool):
    """查询邻近地区工具"""
    
    @property
    def name(self) -> str:
        return "nearby_region_query"
    
    @property
    def description(self) -> str:
        return """查询指定地区邻近的其他地区。
【功能说明】
基于知识图谱中的地区层级关系和地理位置邻近性，查询指定地区周边的其他区县或城市，
帮助用户了解目的地周边的文化资源分布。

【数据结构】
知识图谱存储结构：
- 节点类型：Region（地区），包含 name、level（省/市/区/县）、latitude、longitude 等属性
- 边类型：NEAR（地区间邻近关系）、CONTAINS（包含关系，如西安市包含雁塔区）
- 查询机制：Cypher 查询 MATCH (r:Region {name: $name})-[r:NEAR|CONTAINS]-(other:Region)

【应用场景】
1. 用户请求添加项目时：了解目的地周边还有哪些地区有非遗项目
2. 区域旅行规划：规划跨地区的非遗文化之旅
3. 扩大搜索范围：当某地区项目不足时，推荐邻近地区的项目

【使用示例】
用户："西安周边还有哪些区县有非遗项目？"
调用：nearby_region_query(region_name="西安市", limit=5)
返回：咸阳、渭南、宝鸡、铜川、商洛等邻近地区列表"""
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "region_name": {
                    "type": "string",
                    "description": "地区名称（如'西安市'、'雁塔区'）"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量限制，默认5",
                    "default": 5
                }
            },
            "required": ["region_name"]
        }
    
    @require_knowledge_graph
    async def execute(self, kg, **kwargs) -> Dict[str, Any]:
        region_name = kwargs.get('region_name')
        limit = kwargs.get('limit', 5)
        
        if not region_name:
            return {
                "success": False,
                "error": "请提供region_name"
            }
        
        try:
            nearby = kg.query_nearby_regions(region_name, limit=limit)
            
            return {
                "success": True,
                "region": region_name,
                "nearby_regions": nearby,
                "count": len(nearby),
                "hint": f"{region_name}周边有{len(nearby)}个邻近地区" if nearby else f"{region_name}暂无邻近地区数据"
            }
        except Exception as e:
            logger.error(f"查询邻近地区失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class RouteHintTool(BaseTool):
    """路线规划提示工具"""
    
    @property
    def name(self) -> str:
        return "heritage_route_hint"
    
    @property
    def description(self) -> str:
        return """获取非遗旅游路线规划提示。
【功能说明】
基于知识图谱的完整关系网络，对已选择的非遗项目进行智能分析，提供路线优化建议、
顺访项目推荐和途经地区提示，帮助用户规划更丰富、更合理的非遗文化之旅。

【数据结构】
知识图谱存储结构：
- 节点：Heritage（非遗项目）、Region（地区）
- 边：NEAR（邻近关系）、LOCATED_AT（位置关系）
- 查询机制：
  * 批量查询多个项目的周边项目
  * 分析项目间的共同地区
  * 计算路线优化建议

【应用场景】
1. 用户请求添加项目时：为已选择的项目推荐可顺访的其他非遗项目
2. 路线规划阶段：优化路线顺序，推荐顺路参观的项目
3. 行程丰富化：在已有行程基础上增加更多文化体验点

【使用示例】
用户："我选择了户县农民画、凤翔木版年画、华县皮影戏，请帮我优化路线"
调用：heritage_route_hint(heritage_ids=[17, 20, 25], departure="西安")
返回：
  - 顺访推荐：3-5个位于路线上的额外非遗项目
  - 路线提示：项目间的途经地区建议
  - 优化建议：如何安排顺序更合理"""
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "heritage_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "非遗项目ID列表"
                },
                "departure": {
                    "type": "string",
                    "description": "出发地（可选）"
                }
            },
            "required": ["heritage_ids"]
        }
    
    @require_knowledge_graph
    async def execute(self, kg, **kwargs) -> Dict[str, Any]:
        heritage_ids = kwargs.get('heritage_ids', [])
        departure = kwargs.get('departure', '')
        
        if not heritage_ids:
            return {
                "success": False,
                "error": "请提供heritage_ids"
            }
        
        try:
            all_nearby = {}
            for hid in heritage_ids:
                nearby = kg.query_nearby_heritages_by_id(hid, limit=3)
                if nearby:
                    all_nearby[hid] = nearby
            
            recommendations = []
            seen_ids = set(heritage_ids)
            for hid, nearby_list in all_nearby.items():
                for item in nearby_list:
                    item_id = item.get('id')
                    if item_id and item_id not in seen_ids:
                        recommendations.append({
                            **item,
                            "nearby_to": hid,
                            "reason": f"邻近已选项目ID:{hid}"
                        })
                        seen_ids.add(item_id)
            
            route_hints = []
            if len(heritage_ids) > 1:
                for i, hid in enumerate(heritage_ids[:-1]):
                    next_hid = heritage_ids[i + 1]
                    nearby_to_first = all_nearby.get(hid, [])
                    nearby_to_second = all_nearby.get(next_hid, [])
                    
                    common_regions = set()
                    for item in nearby_to_first + nearby_to_second:
                        region = item.get('region')
                        if region:
                            common_regions.add(region)
                    
                    if common_regions:
                        route_hints.append({
                            "from_heritage_id": hid,
                            "to_heritage_id": next_hid,
                            "suggested_regions": list(common_regions)[:3],
                            "hint": f"从ID:{hid}到ID:{next_hid}可途经{', '.join(list(common_regions)[:2])}"
                        })
            
            return {
                "success": True,
                "heritage_ids": heritage_ids,
                "nearby_recommendations": recommendations[:5],
                "route_hints": route_hints,
                "total_nearby": len(all_nearby),
                "hint": f"基于知识图谱分析，推荐{len(recommendations[:5])}个可顺访项目" if recommendations else "暂无额外推荐"
            }
        except Exception as e:
            logger.error(f"获取路线提示失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
