export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface LoginCredentials {
  username: string; // matches username field from swagger login
  password: string;
}

export interface QRLoginCredentials {
  qr_token: string;
  pin: string;
}
