import logging
from app.schemas.research_job import JobConditions
from app.services.scrapers.base import BaseAdapter

logger = logging.getLogger(__name__)

class YahooFleaAdapter(BaseAdapter):
    CONDITION_MAP = {
        "new": "new",
        "almost_new": "almost_new",
        "no_scratches": "no_scratches",
        "slight_scratches": "slight_scratches",
        "scratched": "scratched",
        "bad_condition": "bad_condition"
    }

    def build_query(self, conditions: JobConditions) -> dict:
        query_params = {
            "keyword": " ".join(conditions.keywords),
            "status": [],
            "conditions": []
        }

        if conditions.selected_options:
            options = [opt.value for opt in conditions.selected_options]
            if "on_sale" in options:
                query_params["status"].append("on_sale")
            if "sold_out" in options:
                query_params["status"].append("sold_out")
            if "auction" in options:
                logger.warning("Yahoo Flea does not support 'auction' option. Ignoring.")

        if conditions.selected_conditions:
            for cond in conditions.selected_conditions:
                if cond.value in self.CONDITION_MAP:
                    query_params["conditions"].append(self.CONDITION_MAP[cond.value])

        return query_params
