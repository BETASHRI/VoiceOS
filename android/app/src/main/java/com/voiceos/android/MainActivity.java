package com.voiceos.android;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.WebSocket;
import okhttp3.WebSocketListener;

import org.json.JSONObject;

public class MainActivity extends Activity {

    // Change this later to the IP address of the computer running VoiceOS.
    private static final String GATEWAY_URL =
            "ws://192.168.1.100:8000/android/ws";

    private static final String DEVICE_ID = "voiceos-android";

    private TextView statusText;
    private OkHttpClient client;
    private WebSocket webSocket;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        statusText = new TextView(this);
        statusText.setText("VoiceOS Android Bridge\nConnecting...");
        statusText.setPadding(32, 32, 32, 32);
        setContentView(statusText);

        connect();
    }

    private void connect() {
        client = new OkHttpClient();

        Request request = new Request.Builder()
                .url(GATEWAY_URL)
                .build();

        webSocket = client.newWebSocket(
                request,
                new WebSocketListener() {

                    @Override
                    public void onOpen(
                            WebSocket webSocket,
                            okhttp3.Response response) {

                        updateStatus("Connected to VoiceOS");

                        try {
                            JSONObject register = new JSONObject();
                            register.put("type", "register");
                            register.put("device_id", DEVICE_ID);

                            webSocket.send(register.toString());

                        } catch (Exception e) {
                            updateStatus("Registration failed");
                        }
                    }

                    @Override
                    public void onMessage(
                            WebSocket webSocket,
                            String text) {

                        handleMessage(text);
                    }

                    @Override
                    public void onFailure(
                            WebSocket webSocket,
                            Throwable t,
                            okhttp3.Response response) {

                        updateStatus(
                                "Connection failed: " + t.getMessage()
                        );
                    }

                    @Override
                    public void onClosed(
                            WebSocket webSocket,
                            int code,
                            String reason) {

                        updateStatus("Disconnected");
                    }
                }
        );
    }

    private void handleMessage(String text) {
        try {
            JSONObject message = new JSONObject(text);

            String type = message.optString("type");

            if ("command".equals(type)) {
                String commandId =
                        message.optString("command_id");

                String command =
                        message.optString("intent");

                JSONObject params =
                        message.optJSONObject("params");

                executeCommand(
                        commandId,
                        command,
                        params
                );
            }

        } catch (Exception e) {
            updateStatus("Invalid command received");
        }
    }

    private void executeCommand(
            String commandId,
            String command,
            JSONObject params) {

        /*
         * Android command execution will be added here.
         *
         * For now we acknowledge the command so that
         * the WebSocket connection can be tested.
         */

        try {
            JSONObject result = new JSONObject();

            result.put("type", "result");
            result.put("command_id", commandId);
            result.put("success", true);
            result.put("intent", command);
            result.put(
                    "message",
                    "Command received: " + command
            );

            if (webSocket != null) {
                webSocket.send(result.toString());
            }

            updateStatus("Command received: " + command);

        } catch (Exception e) {
            updateStatus("Failed to send command result");
        }
    }

    private void updateStatus(final String message) {
        runOnUiThread(() -> statusText.setText(
                "VoiceOS Android Bridge\n\n" + message
        ));
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();

        if (webSocket != null) {
            webSocket.close(1000, "Activity destroyed");
        }

        if (client != null) {
            client.dispatcher().executorService().shutdown();
        }
    }
                              }
