export type SearchOption = 'on_sale' | 'sold_out' | 'fixed_price' | 'auction';
export type ItemCondition = 'new' | 'almost_new' | 'no_scratches' | 'slight_scratches' | 'scratched' | 'bad_condition';

export interface ResearchConditions {
  keywords: string[];
  sources: string[];
  days_back: number;
  min_sales: number;
  selected_options: SearchOption[];
  selected_conditions: ItemCondition[];
}

export interface ResearchStartPayload {
  title: string;
  conditions: ResearchConditions;
}
