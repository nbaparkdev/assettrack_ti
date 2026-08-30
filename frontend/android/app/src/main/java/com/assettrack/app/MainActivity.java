package com.assettrack.app;

import android.Manifest;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;

import com.getcapacitor.BridgeActivity;

import java.util.ArrayList;
import java.util.List;

public class MainActivity extends BridgeActivity {
    private static final int STARTUP_PERMISSIONS_REQUEST = 4100;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(CameraPermissionsPlugin.class);
        super.onCreate(savedInstanceState);
        requestStartupPermissions();
    }

    private void requestStartupPermissions() {
        List<String> pendingPermissions = new ArrayList<>();

        if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            pendingPermissions.add(Manifest.permission.CAMERA);
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU
                && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            pendingPermissions.add(Manifest.permission.POST_NOTIFICATIONS);
        }

        if (!pendingPermissions.isEmpty()) {
            requestPermissions(pendingPermissions.toArray(new String[0]), STARTUP_PERMISSIONS_REQUEST);
        }
    }
}
