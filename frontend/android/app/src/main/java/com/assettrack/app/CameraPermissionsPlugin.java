package com.assettrack.app;

import android.Manifest;

import com.getcapacitor.JSObject;
import com.getcapacitor.PermissionState;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import com.getcapacitor.annotation.PermissionCallback;

/**
 * Exposes Android's camera permission directly to the QR scanner UI.
 * WebView permission prompts are not reliable on all Android/collector builds,
 * so the scanner requests the OS permission before opening a video stream.
 */
@CapacitorPlugin(
    name = "CameraPermissions",
    permissions = {
        @Permission(strings = { Manifest.permission.CAMERA }, alias = CameraPermissionsPlugin.CAMERA)
    }
)
public class CameraPermissionsPlugin extends Plugin {
    static final String CAMERA = "camera";

    @PluginMethod
    public void checkPermissions(PluginCall call) {
        call.resolve(permissionResult());
    }

    @PluginMethod
    public void requestPermissions(PluginCall call) {
        if (getPermissionState(CAMERA) == PermissionState.GRANTED) {
            call.resolve(permissionResult());
            return;
        }

        requestPermissionForAlias(CAMERA, call, "cameraPermissionCallback");
    }

    @PermissionCallback
    private void cameraPermissionCallback(PluginCall call) {
        call.resolve(permissionResult());
    }

    private JSObject permissionResult() {
        JSObject result = new JSObject();
        result.put("camera", getPermissionState(CAMERA) == PermissionState.GRANTED ? "granted" : "denied");
        return result;
    }
}
