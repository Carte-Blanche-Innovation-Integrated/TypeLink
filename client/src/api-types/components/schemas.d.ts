export interface Error {
    message: string;
    /** @description Short code describing the error */
    code: string;
}

export interface Item {
    id: number;
    name: string;
    description: string;
    /** Format: decimal */
    price?: string;
    /** Format: int64 */
    stock?: number;
}

export interface NotFound {
    detail: string;
}

export interface PatchedItem {
    id?: number;
    name?: string;
    description?: string;
    /** Format: decimal */
    price?: string;
    /** Format: int64 */
    stock?: number;
}
