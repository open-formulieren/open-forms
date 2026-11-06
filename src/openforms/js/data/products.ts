export interface Product {
  url: string;
  uuid: string;
  name: string;
  price: string | null;
  information: string;
  producttypeUuid: string | null;
  productSource: 'local' | 'open_product';
}
