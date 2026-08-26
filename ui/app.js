class JarvisAudioVisualizer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.idle = true;
        this.audioCtx = null;
        this.analyser = null;
        this.dataArray = null;
        this.animationFrame = null;
        this.rotation = 0;
        
        this.resize();
        window.addEventListener('resize', () => this.resize());
    }

    resize() {
        const dpr = window.devicePixelRatio || 1;
        const rect = this.canvas.parentElement.getBoundingClientRect();
        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        this.ctx.scale(dpr, dpr);
        this.width = rect.width;
        this.height = rect.height;
    }

    async initMic() {
        try {
            if (!this.audioCtx) {
                this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }
            if (this.audioCtx.state === 'suspended') {
                await this.audioCtx.resume();
            }
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
            const source = this.audioCtx.createMediaStreamSource(stream);
            this.analyser = this.audioCtx.createAnalyser();
            this.analyser.fftSize = 256;
            this.analyser.smoothingTimeConstant = 0.82;
            source.connect(this.analyser);
            this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
            this.idle = false;
        } catch (e) {
            console.error("Audio access denied or failed", e);
            this.idle = true;
        }
    }

    startIdle() {
        this.idle = true;
    }

    stopIdle() {
        this.idle = false;
    }

    render() {
        this.ctx.clearRect(0, 0, this.width, this.height);
        
        let avgFreq = 0;
        if (!this.idle && this.analyser) {
            this.analyser.getByteFrequencyData(this.dataArray);
            let sum = 0;
            for (let i = 0; i < this.dataArray.length; i++) {
                sum += this.dataArray[i];
            }
            avgFreq = sum / this.dataArray.length;
        } else {
            avgFreq = 20 + Math.sin(Date.now() / 500) * 10;
        }

        const cx = this.width / 2;
        const cy = this.height / 2;
        const baseRadius = 40 + (avgFreq * 0.2);

        this.ctx.shadowBlur = 15;
        this.ctx.shadowColor = '#00f3ff';

        const grad = this.ctx.createRadialGradient(cx, cy, 0, cx, cy, baseRadius);
        grad.addColorStop(0, 'rgba(0, 243, 255, 0.8)');
        grad.addColorStop(1, 'rgba(0, 243, 255, 0)');
        this.ctx.fillStyle = grad;
        this.ctx.beginPath();
        this.ctx.arc(cx, cy, baseRadius, 0, Math.PI * 2);
        this.ctx.fill();

        const numBars = 64;
        this.rotation += 0.005;
        this.ctx.save();
        this.ctx.translate(cx, cy);
        this.ctx.rotate(this.rotation);

        for (let i = 0; i < numBars; i++) {
            const angle = (i / numBars) * Math.PI * 2;
            const val = (!this.idle && this.dataArray) ? this.dataArray[i] : (20 + Math.sin(Date.now()/300 + i) * 10);
            const barLength = Math.max(5, val * 0.4);
            
            this.ctx.save();
            this.ctx.rotate(angle);
            this.ctx.translate(baseRadius + 10, 0);
            
            const barGrad = this.ctx.createLinearGradient(0, 0, barLength, 0);
            barGrad.addColorStop(0, '#00f3ff');
            barGrad.addColorStop(1, '#ffffff');
            
            this.ctx.fillStyle = barGrad;
            this.ctx.beginPath();
            this.ctx.roundRect(0, -2, barLength, 4, 2);
            this.ctx.fill();
            this.ctx.restore();
        }

        this.ctx.restore();
        
        this.animationFrame = requestAnimationFrame(() => this.render());
    }
}

class ConstellationParticleField {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.numParticles = 45;
        
        this.resize();
        window.addEventListener('resize', () => this.resize());
        
        for (let i = 0; i < this.numParticles; i++) {
            this.particles.push({
                x: Math.random() * this.width,
                y: Math.random() * this.height,
                vx: (Math.random() - 0.5) * 1,
                vy: (Math.random() - 0.5) * 1
            });
        }
        
        this.animate();
    }

    resize() {
        const dpr = window.devicePixelRatio || 1;
        this.width = window.innerWidth;
        this.height = window.innerHeight;
        this.canvas.width = this.width * dpr;
        this.canvas.height = this.height * dpr;
        this.ctx.scale(dpr, dpr);
    }

    animate() {
        this.ctx.clearRect(0, 0, this.width, this.height);
        
        for (let i = 0; i < this.particles.length; i++) {
            const p = this.particles[i];
            p.x += p.vx;
            p.y += p.vy;
            
            if (p.x < 0 || p.x > this.width) p.vx *= -1;
            if (p.y < 0 || p.y > this.height) p.vy *= -1;
            
            this.ctx.fillStyle = '#00f3ff';
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, 1.5, 0, Math.PI * 2);
            this.ctx.fill();
            
            for (let j = i + 1; j < this.particles.length; j++) {
                const p2 = this.particles[j];
                const dx = p.x - p2.x;
                const dy = p.y - p2.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                
                if (dist < 100) {
                    this.ctx.strokeStyle = `rgba(0, 243, 255, ${1 - dist / 100})`;
                    this.ctx.lineWidth = 0.5;
                    this.ctx.beginPath();
                    this.ctx.moveTo(p.x, p.y);
                    this.ctx.lineTo(p2.x, p2.y);
                    this.ctx.stroke();
                }
            }
        }
        
        requestAnimationFrame(() => this.animate());
    }
}

class SmoothStreamWriter {
    constructor(targetElId, charsPerSecond = 60) {
        this.targetEl = document.getElementById(targetElId);
        if (!this.targetEl) {
            // Find the active caret or element
            this.targetEl = document.querySelector(targetElId);
        }
        this.charsPerSecond = charsPerSecond;
        this.buffer = '';
        this.interval = null;
        this.isComplete = false;
        this.renderedText = '';
        this.caretHtml = '<span class="hud-caret"></span>';
    }

    pushChunk(chunk) {
        this.buffer += chunk;
        if (!this.interval && !this.isComplete) {
            this.startTyping();
        }
    }

    startTyping() {
        const delay = 1000 / this.charsPerSecond;
        this.interval = setInterval(() => {
            if (this.buffer.length > 0) {
                let charsToTake = 1;
                if (this.buffer.length > 50) charsToTake = 3;
                if (this.buffer.length > 100) charsToTake = 5;
                
                const chunk = this.buffer.substring(0, charsToTake);
                this.renderedText += chunk;
                this.buffer = this.buffer.substring(charsToTake);
                this.updateDOM();
            } else if (this.isComplete) {
                clearInterval(this.interval);
                this.interval = null;
                this.updateDOM(true); // final render without caret
            }
        }, delay);
    }

    updateDOM(final = false) {
        let displayHtml = this.escapeHtml(this.renderedText);
        // Simple markdown code block support
        displayHtml = displayHtml.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        
        if (!final) {
            this.targetEl.innerHTML = displayHtml + this.caretHtml;
        } else {
            this.targetEl.innerHTML = displayHtml;
        }
        
        const terminal = document.getElementById('terminal');
        terminal.scrollTop = terminal.scrollHeight;
    }

    completeImmediately() {
        this.isComplete = true;
        if (this.buffer.length > 0) {
            this.renderedText += this.buffer;
            this.buffer = '';
        }
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
        this.updateDOM(true);
    }
    
    escapeHtml(unsafe) {
        return unsafe
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;");
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new ConstellationParticleField('constellationCanvas');
    const visualizer = new JarvisAudioVisualizer('jarvisVisualizer');
    visualizer.render();

    document.body.classList.add('revealed');

    const updateTime = () => {
        const now = new Date();
        document.getElementById('uptimeClock').textContent = 
            now.getHours().toString().padStart(2, '0') + ':' + 
            now.getMinutes().toString().padStart(2, '0') + ':' + 
            now.getSeconds().toString().padStart(2, '0');
    };
    setInterval(updateTime, 1000);
    updateTime();

    const fetchStats = async () => {
        try {
            const res = await fetch('/api/system-stats');
            if (res.ok) {
                const data = await res.json();
                document.getElementById('cpuStat').textContent = data.cpu;
                document.getElementById('ramStat').textContent = data.ram;
                document.getElementById('batteryStat').textContent = data.battery;
            }
        } catch (e) {
            console.log("Stats fetch failed");
        }
    };
    setInterval(fetchStats, 5000);
    fetchStats();

    const terminal = document.getElementById('terminal');
    const appendMessage = (role, text) => {
        const msgDiv = document.createElement('div');
        msgDiv.className = `msg msg-${role}`;
        
        if (role === 'noctis') {
            msgDiv.id = 'msg-' + Date.now();
        } else {
            msgDiv.textContent = text;
        }
        
        terminal.appendChild(msgDiv);
        terminal.scrollTop = terminal.scrollHeight;
        return msgDiv;
    };

    let ws = null;
    let reconnectTimeout = 1000;
    let currentStreamWriter = null;

    const connectWs = () => {
        ws = new WebSocket(`ws://${window.location.host}/ws`);
        
        ws.onopen = () => {
            reconnectTimeout = 1000;
            console.log('WS Connected');
        };

        ws.onmessage = (e) => {
            const msg = JSON.parse(e.data);
            if (msg.event === 'status') {
                const badge = document.getElementById('statusBadge');
                badge.textContent = msg.data.toUpperCase();
                badge.className = 'status-badge ' + (msg.data === 'listening' || msg.data === 'processing' ? 'active' : 'standby');
            } else if (msg.event === 'voice_state') {
                document.getElementById('voiceLabel').textContent = 'Voice: ' + msg.data;
                if (msg.data === 'listening') {
                    visualizer.initMic();
                } else if (msg.data === 'idle') {
                    visualizer.startIdle();
                }
            } else if (msg.event === 'transcription') {
                appendMessage('user', msg.data);
            } else if (msg.event === 'llm_token') {
                if (!currentStreamWriter) {
                    const msgDiv = appendMessage('noctis', '');
                    currentStreamWriter = new SmoothStreamWriter('#' + msgDiv.id);
                }
                currentStreamWriter.pushChunk(msg.data);
            } else if (msg.event === 'llm_done') {
                if (currentStreamWriter) {
                    currentStreamWriter.completeImmediately();
                    currentStreamWriter = null;
                }
            }
        };

        ws.onclose = () => {
            setTimeout(connectWs, Math.min(reconnectTimeout, 10000));
            reconnectTimeout *= 2;
        };
    };
    connectWs();

    const input = document.getElementById('commandInput');
    const sendBtn = document.getElementById('sendBtn');

    document.querySelectorAll('.quick-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const cmd = btn.getAttribute('data-cmd');
            if (cmd) {
                input.value = cmd;
                sendMessage();
            }
        });
    });

    const sendMessage = async () => {
        const text = input.value.trim();
        if (!text) return;
        input.value = '';
        
        appendMessage('user', text);
        const msgDiv = appendMessage('noctis', '');
        const writer = new SmoothStreamWriter('#' + msgDiv.id, 80);
        
        try {
            const res = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            const data = await res.json();
            writer.pushChunk(data.response);
            writer.completeImmediately();
        } catch (e) {
            writer.pushChunk("Error: Connection failed.");
            writer.completeImmediately();
        }
    };

    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    sendBtn.addEventListener('click', sendMessage);

    document.getElementById('closeBtn').addEventListener('click', () => {
        fetch('/api/shutdown', { method: 'POST' });
        window.close();
    });
    document.getElementById('minimizeBtn').addEventListener('click', () => {
        // usually handled by backend/webview APIs, ignored here or handled by external wrapper
    });
});
