"""
MOI数据库客户端服务
用于查询内部数据源（采购项目、供应商、价格等）
"""

import logging
import httpx
from typing import Dict, Any, Optional, List
from src.config import settings

logger = logging.getLogger(__name__)


class MOIClient:
    """MOI数据库API客户端"""
    
    def __init__(self):
        self.base_url = settings.MOI_BASE_URL
        self.api_key = settings.MOI_API_KEY
        self.timeout = 30.0
    
    async def run_sql(self, statement: str) -> Dict[str, Any]:
        """
        执行SQL查询
        
        Args:
            statement: SQL语句
            
        Returns:
            查询结果，包含columns和rows
        """
        url = f"{self.base_url}/catalog/nl2sql/run_sql"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'moi-key': self.api_key
        }
        
        payload = {
            "operation": "run_sql",
            "statement": statement
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"MOI API错误: {response.status_code} - {error_text}")
                    return {
                        "error": f"API请求失败: {response.status_code} - {error_text}",
                        "columns": [],
                        "rows": []
                    }
                
                data = response.json()
                logger.info(f"MOI API响应: {data.get('code', 'Unknown')}")
                
                # 解析API响应
                if data.get('code') != 'OK':
                    return {
                        "error": data.get('msg', '查询失败'),
                        "columns": [],
                        "rows": []
                    }
                
                # 解析结果
                results = data.get('data', {}).get('results', [])
                if not results:
                    return {
                        "columns": [],
                        "rows": []
                    }
                
                result = results[0]
                columns = result.get('columns', []) or []
                raw_rows = result.get('rows') or []
                
                # 将二维数组转换为对象数组
                rows = []
                if raw_rows:
                    for row in raw_rows:
                        obj = {}
                        for idx, col in enumerate(columns):
                            obj[col] = row[idx] if idx < len(row) else None
                        rows.append(obj)
                
                return {
                    "columns": columns,
                    "rows": rows
                }
                
        except httpx.TimeoutException:
            logger.error("MOI API请求超时")
            return {
                "error": "请求超时",
                "columns": [],
                "rows": []
            }
        except Exception as e:
            logger.exception(f"MOI SQL执行错误: {e}")
            return {
                "error": str(e),
                "columns": [],
                "rows": []
            }


# 全局客户端实例
_moi_client: Optional[MOIClient] = None


def get_moi_client() -> MOIClient:
    """获取MOI客户端实例（单例模式）"""
    global _moi_client
    if _moi_client is None:
        _moi_client = MOIClient()
    return _moi_client

