export interface Product {
  url: string;
  uuid: string;
  name: string;
  price: string | null;
  information: string;
  productSource: 'local' | 'open_product';
}
