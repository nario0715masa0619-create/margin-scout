# Source Adapter Matrix & 実装ガイド

## 1. 概要
各ソース（取得元サイト）は、検索オプションおよびコンディションのフィルタリングにおいて対応できる項目が異なります。本ドキュメントは、各ソースがどの条件に対応可能かを定義し、Adapter クラスでどのようにクエリやフィルタリングを実装するかのガイドラインを提供します。

## 2. 対応可否マトリクス

### 2.1 検索オプション (Search Options)
| オプション | 定義 | Mercari | Yahoo Flea | Yahoo Auction | Hardoff |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **`on_sale`** | 販売中 | ✅ | ✅ | ✅ | ✅ |
| **`sold_out`** | 売り切れ | ✅ | ✅ | ✅ | ❌ |
| **`fixed_price`** | 通常出品（即決）| ✅ (デフォルト) | ✅ (デフォルト) | ✅ | ✅ |
| **`auction`** | オークション | ❌ | ❌ | ✅ | ❌ |

> [!WARNING]
> `auction` は Yahoo!オークション 固有の機能です。他のソースで `auction` が選択されていても、そのソースの検索結果には反映されません（またはスキップされます）。

### 2.2 コンディション (Conditions)
| コンディション | 定義 | Mercari | Yahoo Flea | Yahoo Auction | Hardoff |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **`new`** | 新品、未使用 | ✅ | ✅ | ✅ | ✅ (Sランク等) |
| **`almost_new`** | 未使用に近い | ✅ | ✅ | ✅ | ✅ (Aランク等) |
| **`no_scratches`** | 目立った傷や汚れなし | ✅ | ✅ | ✅ | ✅ (Bランク等) |
| **`slight_scratches`** | やや傷や汚れあり | ✅ | ✅ | ✅ | ✅ (Cランク等) |
| **`scratched`** | 傷や汚れあり | ✅ | ✅ | ✅ | ✅ (ジャンク等) |
| **`bad_condition`** | 全体的に状態が悪い | ✅ | ✅ | ✅ | ✅ (ジャンク等) |

> [!NOTE]
> サイトごとの内部IDやクエリパラメータマッピングは各アダプタ内で実装します。例えば、Hardoffの場合は商品ランク（S, A, B, C...）へのマッピングを行う必要があります。

## 3. Source Adapter 実装ガイド

各スクレイパーまたはAPIアダプタは、共通のインターフェース（または基底クラス）を継承し、`JobConditions` に基づいて自身のプラットフォーム用の検索クエリを構築します。

### 3.1 実装ポリシー

1. **対応可能条件の抽出**: 
   UIで複数選択された条件リストを受け取り、自プラットフォームでサポートしている条件のみをフィルタリングしてクエリパラメータに変換します。
2. **未対応条件のハンドリング**:
   未対応の条件が指定された場合はエラーとせず、**無視（ログ出力）** または **スキップ** します。
   - 例: Mercariアダプタに `auction` が渡された場合、Mercariにはオークション機能がないため無視し、通常の販売中アイテムとして検索します。
3. **OR条件の原則**:
   配列で渡された複数のオプションやコンディションは、基本的にプラットフォーム側で **OR 条件** として扱います（例：「新品」または「未使用に近い」）。

### 3.2 実装例（Python 疑似コード）

```python
import logging

logger = logging.getLogger(__name__)

class BaseAdapter:
    def build_query(self, conditions: JobConditions) -> dict:
        raise NotImplementedError

class MercariAdapter(BaseAdapter):
    # Mercari の状態IDマッピング例
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
        if "on_sale" in conditions.selected_options:
            query_params["status"].append("on_sale")
        if "sold_out" in conditions.selected_options:
            query_params["status"].append("trading")
            query_params["status"].append("sold_out")
        
        if "auction" in conditions.selected_options:
            logger.warning("Mercari does not support 'auction' option. Ignoring.")

        # コンディションの処理
        for cond in conditions.selected_conditions:
            if cond in self.CONDITION_MAP:
                query_params["item_condition_id"].append(self.CONDITION_MAP[cond])
            else:
                logger.warning(f"Unknown condition '{cond}' for Mercari. Ignoring.")

        return query_params
```

## 4. 統合時の注意点
- **デフォルト挙動**: もし UI 側でコンディションが1つも選択されなかった場合、空配列 `[]` がバックエンドに送信されます。バックエンドのアダプタは、空配列を「すべて許可（条件指定なし）」として解釈するように実装してください。
