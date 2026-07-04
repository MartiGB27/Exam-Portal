class CameraMonitor{
    constructor(){
        this.video = document.getElementById("video");
        this.canvas = document.getElementById("canvas");
        this.ctx = this.canvas.getContext("2d");
        this.ws = null;
        this.active = false;
        this.cheatEvents = [];
        this.token = new URLSearchParams(window.location.search).get("token");
    }

    async start(){
        try{
            const stream = await navigator.mediaDevices.getUserMedia({video: true});
            this.video.srcObject = stream;
            await new Promise(resolve => this.video.onloadedmetadata = resolve);
            this.canvas.width = 320;
            this.canvas.height = 240;
            this.active = true;
            this._connectWebSocket();
            this._startCapture();
            this._watchVisibility();
            this._watchWindowFocus();
        } catch(err){
            console.warn("Camera not available:", err);
            this._updateStatus("🔴", "Camera unavailable");
        }
    }

    _connectWebSocket(){
        const wsUrl = `ws://${window.location.host}/ws/monitor/${this.token}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            this._updateStatus("🟢", "Camera active");
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this._handleDetection(data);
        };

        this.ws.onclose = () => {
            this._updateStatus("🔴", "Connection lost");
            // Retry connection  after 3 seconds
            if (this.active) {
                setTimeout(() => this._connectWebSocket(), 3000);
            }
        };

        this.ws.onerror = () => {
            this._updateStatus("🔴", "Connection error");
        };
    }

    _startCapture(){
        const interval = setInterval(() => {
            if (!this.active) {
                clearInterval(interval);
                return;
            }
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ctx.drawImage(this.video, 0, 0, 320, 240);
                const frame = this.canvas.toDataURL("image/jpeg", 0.6).split(",")[1];
                this.ws.send(JSON.stringify({frame}));
            }
        }, 1000); // Send 1 frame per second
    }

    _handleDetection(data){
        if (data.suspicious) {
            const detail = data.detail || "";
            const type = data.face_detected ? "looking_away" : "no_face";

            this._logEvent(type, detail);

            if (!data.face_detected) {
                this._updateStatus("🔴", "Face not detected");
            } else {
                this._updateStatus("🟡", "Looking away");
            }
        } else {
            this._updateStatus("🟢", "Camera active");
        }
    }

    _watchVisibility(){
        document.addEventListener("visibilitychange", () => {
            if (document.hidden) {
                this._logEvent("tab_switch", "User switched tab or minimized");
                this._updateStatus("🔴", "Tab switch detected");
            } else {
                this._updateStatus("🟢", "Camera active");
            }
        });
    }

    _watchWindowFocus(){
        window.addEventListener("blur", () => {
            this._logEvent("window_blur", "User switched to another application");
            this._updateStatus("🔴", "Window focus lost");
        });

        window.addEventListener("focus", () => {
            this._updateStatus("🟢", "Camera active");
        });
    }

    _logEvent(type, detail = ""){
        this.cheatEvents.push({
            type,
            detail,
            timestamp: new Date().toISOString()
        });
    }

    _updateStatus(icon, text){
        const iconEl = document.getElementById("monitor-icon");
        const textEl = document.getElementById("monitor-text");
        if (iconEl) iconEl.textContent = icon;
        if (textEl) textEl.textContent = text;
    }

    stop(){
        this.active = false;
        if (this.ws) this.ws.close();
        if (this.video.srcObject) {
            this.video.srcObject.getTracks().forEach(t => t.stop());
        }
    }

    getCheatEvents(){
        return this.cheatEvents;
    }
}