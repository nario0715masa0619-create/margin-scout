from app.schemas.research_job import JobConditions

class BaseAdapter:
    def build_query(self, conditions: JobConditions) -> dict:
        """
        検索条件から各プラットフォーム固有のクエリパラメータを構築する
        """
        raise NotImplementedError("Each adapter must implement build_query()")
