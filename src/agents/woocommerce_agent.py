"""
WooCommerce agent responsible for interacting with the WooCommerce API.
"""

from typing import Dict, List, Any, Optional
from woocommerce import API

from utils import get_logger

# יצירת לוגר ייעודי ל-WooCommerce Agent
logger = get_logger(__name__)

class WooCommerceAgent:
    def __init__(self, url: str, consumer_key: str, consumer_secret: str):
        """Initialize WooCommerce API client."""
        self.wcapi = API(
            url=url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            version="wc/v3"
        )
        logger.info(
            "מאתחל את ה-WooCommerce Agent",
            extra={
                "store_url": url,
                "api_version": "wc/v3",
                "consumer_key_length": len(consumer_key) if consumer_key else 0
            }
        )

    def get_products(self, 
                    page: int = 1, 
                    per_page: int = 10, 
                    category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get products from the store.
        
        Args:
            page: Page number
            per_page: Number of items per page
            category: Optional category filter
        """
        try:
            params = {
                "page": page,
                "per_page": per_page
            }
            if category:
                params["category"] = category

            logger.info(
                "מבקש רשימת מוצרים",
                extra={
                    "page": page,
                    "per_page": per_page,
                    "category": category,
                    "params": params
                }
            )

            response = self.wcapi.get("products", params=params)
            
            if response.status_code == 200:
                products = response.json()
                logger.info(
                    "התקבלו מוצרים בהצלחה",
                    extra={
                        "products_count": len(products),
                        "total_pages": response.headers.get('X-WP-TotalPages'),
                        "total_products": response.headers.get('X-WP-Total')
                    }
                )
                return products
            else:
                logger.error(
                    "שגיאה בקבלת מוצרים",
                    extra={
                        "status_code": response.status_code,
                        "response_text": response.text,
                        "params": params
                    }
                )
                return []
        except Exception as e:
            logger.error(
                "שגיאה בקבלת מוצרים",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "params": params
                }
            )
            return []

    def get_orders(self, 
                   status: Optional[str] = None, 
                   page: int = 1, 
                   per_page: int = 10) -> List[Dict[str, Any]]:
        """
        Get orders from the store.
        
        Args:
            status: Optional order status filter
            page: Page number
            per_page: Number of items per page
        """
        try:
            params = {
                "page": page,
                "per_page": per_page
            }
            if status:
                params["status"] = status

            logger.info(
                "מבקש רשימת הזמנות",
                extra={
                    "status": status,
                    "page": page,
                    "per_page": per_page,
                    "params": params
                }
            )

            response = self.wcapi.get("orders", params=params)
            
            if response.status_code == 200:
                orders = response.json()
                logger.info(
                    "התקבלו הזמנות בהצלחה",
                    extra={
                        "orders_count": len(orders),
                        "total_pages": response.headers.get('X-WP-TotalPages'),
                        "total_orders": response.headers.get('X-WP-Total')
                    }
                )
                return orders
            else:
                logger.error(
                    "שגיאה בקבלת הזמנות",
                    extra={
                        "status_code": response.status_code,
                        "response_text": response.text,
                        "params": params
                    }
                )
                return []
        except Exception as e:
            logger.error(
                "שגיאה בקבלת הזמנות",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "params": params
                }
            )
            return []

    def update_product(self, 
                      product_id: int, 
                      data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a product's details.
        
        Args:
            product_id: The ID of the product to update
            data: Dictionary containing the fields to update
        """
        try:
            logger.info(
                "מעדכן מוצר",
                extra={
                    "product_id": product_id,
                    "update_fields": list(data.keys()),
                    "data_preview": str(data)[:200] if len(str(data)) > 200 else str(data)
                }
            )

            response = self.wcapi.put(f"products/{product_id}", data)
            
            if response.status_code in [200, 201]:
                updated_product = response.json()
                logger.info(
                    "מוצר עודכן בהצלחה",
                    extra={
                        "product_id": product_id,
                        "updated_fields": list(data.keys())
                    }
                )
                return updated_product
            else:
                logger.error(
                    "שגיאה בעדכון מוצר",
                    extra={
                        "product_id": product_id,
                        "status_code": response.status_code,
                        "response_text": response.text,
                        "data": data
                    }
                )
                return None
        except Exception as e:
            logger.error(
                "שגיאה בעדכון מוצר",
                extra={
                    "product_id": product_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "data": data
                }
            )
            return None

    def get_sales_report(self, 
                        date_min: Optional[str] = None,
                        date_max: Optional[str] = None) -> Dict[str, Any]:
        """
        Get sales report for a specific period.
        
        Args:
            date_min: Start date in ISO format (YYYY-MM-DD)
            date_max: End date in ISO format (YYYY-MM-DD)
        """
        try:
            params = {}
            if date_min:
                params["date_min"] = date_min
            if date_max:
                params["date_max"] = date_max

            logger.info(
                "מבקש דוח מכירות",
                extra={
                    "date_min": date_min,
                    "date_max": date_max,
                    "params": params
                }
            )

            response = self.wcapi.get("reports/sales", params=params)
            
            if response.status_code == 200:
                report = response.json()
                logger.info(
                    "התקבל דוח מכירות בהצלחה",
                    extra={
                        "report_period": f"{date_min or 'all'} to {date_max or 'now'}",
                        "total_sales": report.get('total_sales'),
                        "total_orders": report.get('total_orders')
                    }
                )
                return report
            else:
                logger.error(
                    "שגיאה בקבלת דוח מכירות",
                    extra={
                        "status_code": response.status_code,
                        "response_text": response.text,
                        "params": params
                    }
                )
                return {}
        except Exception as e:
            logger.error(
                "שגיאה בקבלת דוח מכירות",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "params": params
                }
            )
            return {} 