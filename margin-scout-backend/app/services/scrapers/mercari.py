import logging
from app.schemas.research_job import JobConditions
from app.services.scrapers.base import BaseAdapter

logger = logging.getLogger(__name__)

class MercariAdapter(BaseAdapter):
    CONDITION_MAP = {
        "new": "1",
        "almost_new": "2",
        "no_scratches": "3",
        "slight_scratches": "4",
        "scratched": "5",
        "bad_condition": "6"
    }

    def build_query(self, conditions: JobConditions) -> dict:
        query_params = {
            "keyword": " ".join(conditions.keywords),
            "status": [],
            "item_condition_id": []
        }

        # 検索オプションの処理
        if conditions.selected_options:
            options = [opt.value for opt in conditions.selected_options]
            if "on_sale" in options:
                query_params["status"].append("on_sale")
            if "sold_out" in options:
                query_params["status"].append("trading")
                query_params["status"].append("sold_out")
            if "auction" in options:
                logger.warning("Mercari does not support 'auction' option. Ignoring.")
        else:
            # 未指定の場合はすべてを含めるなどデフォルト挙動
            pass

        # コンディションの処理
        if conditions.selected_conditions:
            for cond in conditions.selected_conditions:
                if cond.value in self.CONDITION_MAP:
                    query_params["item_condition_id"].append(self.CONDITION_MAP[cond.value])
                else:
                    logger.warning(f"Unknown condition '{cond.value}' for Mercari. Ignoring.")

        return query_params
