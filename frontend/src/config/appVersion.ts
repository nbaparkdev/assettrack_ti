export const APP_CONFIG = {
  CURRENT_VERSION_NAME: import.meta.env.VITE_APP_VERSION_NAME ?? '1.2.0',
  CURRENT_VERSION_CODE: Number(import.meta.env.VITE_APP_VERSION_CODE ?? 2),
  BUILD_TIMESTAMP: import.meta.env.VITE_APP_BUILD_TIMESTAMP ?? '',
  APP_NAME: 'AssetTrack TI',
  PLATFORM_ANDROID: 'Android 7.0+',
};
