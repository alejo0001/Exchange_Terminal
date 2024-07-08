export interface IPriceGroup {
    rangeValue: number;
    prices: number[];
    minPrice: number;
    maxPrice: number;
    sellZone: IEntranceZone;
    buyZone: IEntranceZone;

   
}

export interface IEntranceZone  {
    minPrice: number;
    maxPrice: number;
    zoneType: number;
    priceGroup: IPriceGroup;

  
}

