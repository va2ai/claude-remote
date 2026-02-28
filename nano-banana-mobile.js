/* ============================================================
   CONSTANTS
   ============================================================ */
const MODELS = [
  { id: "gemini-3.1-flash-image-preview", name: "Nano Banana 2", badge: "3.1 Flash", accent: "#FFD600", desc: "Speed & volume optimized", resolutions: ["512px","1K","2K","4K"], maxImages: 4, supportsImageSearch: true, thinkingLevels: ["none","minimal","low","medium","high"] },
  { id: "gemini-3-pro-image-preview", name: "Nano Banana Pro", badge: "3 Pro", accent: "#FF8C00", desc: "Pro asset production", resolutions: ["1K","2K","4K"], maxImages: 4, supportsImageSearch: false, thinkingLevels: ["none","low","high"] },
  { id: "gemini-2.5-flash-image", name: "Nano Banana", badge: "2.5", accent: "#FFAB00", desc: "Fast & efficient", resolutions: ["1K"], maxImages: 1, supportsImageSearch: false, thinkingLevels: ["none"] },
];
const RATIOS = ["1:1","2:3","3:2","3:4","4:3","9:16","16:9"];
const RESOLUTIONS = ["512px","1K","2K","4K"];
const THINKING_LEVELS = ["none","minimal","low","medium","high"];
const TEMPLATES = [
  { icon: "📦", label: "Product", prompt: "A high-resolution, studio-lit product photograph of a sleek {product} resting on {surface}. Three-point softbox lighting with soft reflections. Ultra-realistic, sharp focus. 4:3 aspect ratio.", defaults: { product: "matte-black wireless earbud case", surface: "a marble surface" } },
  { icon: "🎨", label: "Sticker", prompt: "A kawaii-style sticker of a happy {animal} holding a tiny glowing {object}. Colorful, bold outlines, clean vector style, transparent background. No text.", defaults: { animal: "red panda", object: "banana" } },
  { icon: "✏️", label: "Logo", prompt: "Create a modern, minimalist logo for a {business_type} called \"{business_name}\" with elegant serif typography. A {icon_element} icon is subtly integrated into the letter {letter}. {color_scheme}.", defaults: { business_type: "coffee shop", business_name: "The Daily Grind", icon_element: "coffee cup", letter: "D", color_scheme: "Cream background with dark brown accents" } },
  { icon: "🏙️", label: "Isometric", prompt: "A clear, 45-degree top-down isometric miniature 3D cartoon scene of {city} at {time_of_day}, featuring {landmarks}. Soft refined textures with realistic PBR materials and gentle lifelike lighting. Clean minimalistic composition with a dark background.", defaults: { city: "Tokyo", time_of_day: "night", landmarks: "Tokyo Tower, Shibuya crossing, cherry blossoms, and glowing neon signs" } },
  { icon: "🐕", label: "3D Icon", prompt: "An icon representing a cute {subject}. The background is {background_color}. Make the icon in a colorful and tactile 3D style with soft realistic shadows. No text.", defaults: { subject: "golden retriever puppy sitting and looking at the camera", background_color: "white" } },
  { icon: "🌄", label: "Landscape", prompt: "A breathtaking panoramic photograph of {location} at {lighting}. {scene_details}. Shot with a wide-angle lens. Vivid, rich colors with a warm atmospheric glow.", defaults: { location: "Norwegian fjords", lighting: "golden hour", scene_details: "Mirror-like water reflections, dramatic cliff faces, a single red wooden cabin on the shore" } },
  { icon: "💬", label: "Comic", prompt: "Make a {panel_count}-panel comic strip in a clean, modern cartoon style. {story}. Bold colors, speech bubbles with text.", defaults: { panel_count: "3", story: "A programmer is debugging code late at night. Panel 1: staring at screen confused. Panel 2: adds a single semicolon. Panel 3: everything works, triumphant pose" } },
  { icon: "🍽️", label: "Food", prompt: "A professional overhead food photograph of a beautifully plated {dish} on a {table_surface}. Soft natural window light from the left. {garnish_details}. Shot on a 50mm lens.", defaults: { dish: "bowl of ramen", table_surface: "dark wooden table", garnish_details: "Steam rising from the broth. Garnished with a soft-boiled egg, nori, green onions, and chashu pork" } },
  { icon: "🌐", label: "Weather", prompt: "Generate an infographic of the current weather in {city} with temperatures, conditions and a {forecast_range} forecast. Modern flat design with weather icons.", grounding: true, defaults: { city: "Tokyo", forecast_range: "3-day" } },
];

/* ============================================================
   VEO CONSTANTS
   ============================================================ */
const VEO_MODEL = {
  id: "veo-2.0-generate-001",
  name: "Veo 2",
  badge: "Veo 2",
  accent: "#7C3AED",
  desc: "Image to video",
};
const VIDEO_DURATIONS = [5, 8];
const VIDEO_RATIOS = ["16:9", "9:16", "1:1"];

/* ============================================================
   VUE APP
   ============================================================ */
const { createApp } = Vue;

createApp({
  data() {
    return {
      MODELS,
      RATIOS,
      RESOLUTIONS,
      THINKING_LEVELS,
      TEMPLATES,
      VEO_MODEL,
      VIDEO_DURATIONS,
      VIDEO_RATIOS,
      // Key gate
      apiKeyInput: "",
      appActive: false,
      API_KEY: "",
      // Core selection state
      selectedModel: 0,
      selectedRatio: "1:1",
      selectedRes: "1K",
      thinkingLevel: "none",
      // Generation state
      isGenerating: false,
      results: [],
      numImages: 1,
      // Toggles
      personGeneration: true,
      includeTextOutput: true,
      googleSearchEnabled: false,
      imageSearchEnabled: false,
      // Image upload
      uploadedImageData: null,
      uploadedImageMime: null,
      uploadedImageName: null,
      // Mode: image | video
      mode: "image",
      veoDuration: 5,
      veoRatio: "16:9",
      isPolling: false,
      // Template modal
      activeTemplateIndex: null,
      tplVarValues: {},
      // UI state
      sidebarCollapsed: false,
      sheetOpen: false,
      tplSheetOpen: false,
      errorMessage: "",
      promptText: "",
    };
  },

  computed: {
    currentModel() {
      return MODELS[this.selectedModel];
    },
    availableResolutions() {
      return RESOLUTIONS.map(r => ({
        value: r,
        available: this.currentModel.resolutions.includes(r),
        selected: r === this.selectedRes,
      }));
    },
    availableThinkingLevels() {
      return THINKING_LEVELS.map(t => ({
        value: t,
        label: t === "none" ? "Off" : t.charAt(0).toUpperCase() + t.slice(1),
        available: this.currentModel.thinkingLevels.includes(t),
        selected: t === this.thinkingLevel,
      }));
    },
    canImageSearch() {
      return this.currentModel.supportsImageSearch;
    },
    canDecrement() {
      return this.numImages > 1;
    },
    canIncrement() {
      return this.numImages < this.currentModel.maxImages;
    },
    sendBtnDisabled() {
      if (this.mode === "video") return !this.promptText.trim() || this.isGenerating;
      return !this.promptText.trim() || this.isGenerating;
    },
    activePills() {
      if (this.mode === "video") {
        const pills = [
          { label: VEO_MODEL.badge, on: false, style: "border-color:#7C3AED44;color:#a78bfa;" },
          { label: this.veoRatio, on: false },
          { label: `${this.veoDuration}s`, on: false },
        ];
        if (this.uploadedImageData) pills.push({ label: "🎬 Img→Vid", on: true, style: "border-color:#7C3AED44;color:#C084FC;" });
        return pills;
      }
      const model = this.currentModel;
      const pills = [
        { label: model.badge, on: false },
        { label: this.selectedRatio, on: false },
        { label: this.selectedRes, on: false },
      ];
      if (this.numImages > 1) pills.push({ label: `${this.numImages}x`, on: true });
      if (this.googleSearchEnabled) pills.push({ label: "🔍", on: true, style: "border-color:#22c55e44;color:#4ADE80;" });
      if (this.imageSearchEnabled && model.supportsImageSearch) pills.push({ label: "🖼️", on: true, style: "border-color:#3b82f644;color:#60A5FA;" });
      if (this.thinkingLevel !== "none") pills.push({ label: `🧠 ${this.thinkingLevel}`, on: true });
      if (!this.personGeneration) pills.push({ label: "👤", on: true, style: "border-color:#ef444444;color:#FF4D4D;" });
      if (!this.includeTextOutput) pills.push({ label: "IMG", on: true });
      if (this.uploadedImageData) pills.push({ label: "🖌️ Edit", on: true, style: "border-color:#a855f744;color:#C084FC;" });
      return pills;
    },
    templateList() {
      return TEMPLATES.map(t => ({
        ...t,
        hasVars: /\{\w+\}/.test(t.prompt),
      }));
    },
    tplPreviewHtml() {
      if (this.activeTemplateIndex === null) return "";
      const tpl = TEMPLATES[this.activeTemplateIndex];
      const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      return esc(tpl.prompt).replace(/\{(\w+)\}/g, (m, v) => {
        const val = this.tplVarValues[v] && this.tplVarValues[v].trim();
        if (val) return `<span class="tpl-var-filled">${esc(val)}</span>`;
        return `<span class="tpl-var-highlight">{${v}}</span>`;
      });
    },
    tplVarList() {
      if (this.activeTemplateIndex === null) return [];
      const tpl = TEMPLATES[this.activeTemplateIndex];
      const regex = /\{(\w+)\}/g;
      const seen = new Set();
      const vars = [];
      let match;
      while ((match = regex.exec(tpl.prompt)) !== null) {
        if (!seen.has(match[1])) { seen.add(match[1]); vars.push(match[1]); }
      }
      return vars.map(v => ({
        key: v,
        label: v.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()),
        placeholder: `Enter ${v.replace(/_/g, " ").toLowerCase()}...`,
      }));
    },
    uploadPreviewSrc() {
      if (!this.uploadedImageData) return "";
      return `data:${this.uploadedImageMime};base64,${this.uploadedImageData}`;
    },
    promptPlaceholder() {
      if (this.mode === "video") {
        return this.uploadedImageData ? "Describe the motion or action..." : "Upload an image, then describe the motion...";
      }
      return this.uploadedImageData ? "Describe edits to make..." : "Describe an image...";
    },
    resultsLabel() {
      const total = this.results.length;
      const hasVideo = this.results.some(r => r.video);
      const hasImage = this.results.some(r => !r.video);
      if (hasVideo && hasImage) return `Results (${total})`;
      if (hasVideo) return `Generated Videos (${total})`;
      return `Generated Images (${total})`;
    },
  },

  watch: {
    selectedModel(newVal) {
      const model = MODELS[newVal];
      if (!model.resolutions.includes(this.selectedRes)) this.selectedRes = model.resolutions[0];
      if (!model.thinkingLevels.includes(this.thinkingLevel)) this.thinkingLevel = "none";
      if (this.numImages > model.maxImages) this.numImages = model.maxImages;
      if (!model.supportsImageSearch) this.imageSearchEnabled = false;
    },
    results(newVal, oldVal) {
      if (newVal.length > oldVal.length) {
        this.$nextTick(() => {
          const sc = this.$refs.scrollContent;
          if (sc) sc.scrollTop = sc.scrollHeight;
        });
      }
    },
  },

  mounted() {
    // Swipe-down to close settings sheet
    const sheet = this.$refs.settingsSheet;
    if (sheet) {
      let sheetStartY = 0;
      sheet.addEventListener("touchstart", e => { sheetStartY = e.touches[0].clientY; }, { passive: true });
      sheet.addEventListener("touchmove", e => {
        const dy = e.touches[0].clientY - sheetStartY;
        if (dy > 80 && sheet.scrollTop <= 0) this.closeSheet();
      }, { passive: true });
    }

    // Swipe-down to close template modal
    const tplSheet = this.$refs.tplSheet;
    if (tplSheet) {
      let tplStartY = 0;
      tplSheet.addEventListener("touchstart", e => { tplStartY = e.touches[0].clientY; }, { passive: true });
      tplSheet.addEventListener("touchmove", e => {
        const dy = e.touches[0].clientY - tplStartY;
        if (dy > 80 && tplSheet.scrollTop <= 0) this.closeTemplateModal();
      }, { passive: true });
    }

    // Global Escape to close template modal
    document.addEventListener("keydown", e => {
      if (this.tplSheetOpen && e.key === "Escape") this.closeTemplateModal();
    });
  },

  methods: {
    /* ─── MODE ─── */
    switchMode(m) {
      if (this.mode === m) return;
      this.mode = m;
      this.errorMessage = "";
    },

    /* ─── KEY GATE ─── */
    launch() {
      const key = this.apiKeyInput.trim();
      if (!key) return;
      this.API_KEY = key;
      this.appActive = true;
    },
    resetKey() {
      this.API_KEY = "";
      this.apiKeyInput = "";
      this.appActive = false;
    },

    /* ─── MODEL / CHIP SELECTION ─── */
    selectModel(i) {
      this.selectedModel = i;
    },
    selectRatio(r) { this.selectedRatio = r; },
    selectRes(r) { this.selectedRes = r; },
    selectThinking(t) { this.thinkingLevel = t; },

    /* ─── STEPPER ─── */
    changeNumImages(delta) {
      this.numImages = Math.max(1, Math.min(this.currentModel.maxImages, this.numImages + delta));
    },

    /* ─── TOGGLES ─── */
    togglePerson()     { this.personGeneration = !this.personGeneration; },
    toggleTextOutput() { this.includeTextOutput = !this.includeTextOutput; },
    toggleSearch()     { this.googleSearchEnabled = !this.googleSearchEnabled; },
    toggleImageSearch() {
      if (!this.currentModel.supportsImageSearch) return;
      this.imageSearchEnabled = !this.imageSearchEnabled;
    },

    /* ─── SHEET ─── */
    openSheet() {
      this.sheetOpen = true;
      document.body.style.overflow = "hidden";
    },
    closeSheet() {
      this.sheetOpen = false;
      document.body.style.overflow = "";
    },

    /* ─── TEMPLATE MODAL ─── */
    useTemplate(i) {
      const tpl = TEMPLATES[i];
      const vars = this._parseTemplateVars(tpl.prompt);
      if (vars.length > 0) {
        this.showTemplateModal(i);
      } else {
        this._applyPromptText(tpl.prompt, tpl);
      }
    },
    showTemplateModal(index) {
      const tpl = TEMPLATES[index];
      const vars = this._parseTemplateVars(tpl.prompt);
      const vals = {};
      vars.forEach(v => { vals[v] = (tpl.defaults && tpl.defaults[v]) || ""; });
      this.tplVarValues = vals;
      this.activeTemplateIndex = index;
      this.tplSheetOpen = true;
      document.body.style.overflow = "hidden";
      this.$nextTick(() => {
        setTimeout(() => {
          const first = this.$el.querySelector(".tpl-field-input");
          if (first) { first.focus(); first.select(); }
        }, 400);
      });
    },
    closeTemplateModal() {
      this.tplSheetOpen = false;
      this.activeTemplateIndex = null;
      document.body.style.overflow = "";
    },
    confirmTemplate() {
      if (this.activeTemplateIndex === null) return;
      const tpl = TEMPLATES[this.activeTemplateIndex];
      let prompt = tpl.prompt;
      Object.entries(this.tplVarValues).forEach(([v, val]) => {
        const resolved = (val && val.trim()) || (tpl.defaults && tpl.defaults[v]) || "";
        prompt = prompt.replace(new RegExp("\\{" + v + "\\}", "g"), resolved);
      });
      this.closeTemplateModal();
      this._applyPromptText(prompt, tpl);
    },
    _parseTemplateVars(promptStr) {
      const regex = /\{(\w+)\}/g;
      const seen = new Set();
      const vars = [];
      let match;
      while ((match = regex.exec(promptStr)) !== null) {
        if (!seen.has(match[1])) { seen.add(match[1]); vars.push(match[1]); }
      }
      return vars;
    },
    _applyPromptText(prompt, tpl) {
      this.promptText = prompt;
      this.$nextTick(() => {
        if (this.$refs.promptArea) {
          this.autoResize(this.$refs.promptArea);
          this.$refs.promptArea.focus();
        }
      });
      if (tpl && tpl.grounding && !this.googleSearchEnabled) {
        this.googleSearchEnabled = true;
      }
    },

    /* ─── IMAGE UPLOAD ─── */
    handleImageUpload(event) {
      const file = event.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (e) => {
        this.uploadedImageMime = file.type;
        this.uploadedImageData = e.target.result.split(",")[1];
        this.uploadedImageName = file.name;
      };
      reader.readAsDataURL(file);
    },
    removeUploadedImage() {
      this.uploadedImageData = null;
      this.uploadedImageMime = null;
      this.uploadedImageName = null;
      if (this.$refs.imageUpload) this.$refs.imageUpload.value = "";
    },

    /* ─── AUTO RESIZE TEXTAREA ─── */
    autoResize(el) {
      el.style.height = "auto";
      el.style.height = Math.min(el.scrollHeight, 120) + "px";
    },

    /* ─── BUILD REQUEST ─── */
    buildRequestBody(prompt) {
      const model = this.currentModel;
      const modalities = this.includeTextOutput ? ["TEXT", "IMAGE"] : ["IMAGE"];
      const parts = [{ text: prompt }];
      if (this.uploadedImageData) {
        parts.push({ inlineData: { mimeType: this.uploadedImageMime, data: this.uploadedImageData } });
      }
      const body = {
        contents: [{ parts }],
        generationConfig: {
          responseModalities: modalities,
          imageConfig: {
            aspectRatio: this.selectedRatio,
          },
        },
      };
      if (this.selectedRes !== "1K") body.generationConfig.imageConfig.imageSize = this.selectedRes;
      if (this.numImages > 1) body.generationConfig.imageConfig.numberOfImages = this.numImages;
      const tools = [];
      if (this.googleSearchEnabled && !this.imageSearchEnabled) {
        tools.push({ googleSearch: {} });
      } else if (this.googleSearchEnabled && this.imageSearchEnabled && model.supportsImageSearch) {
        tools.push({ google_search: { searchTypes: { webSearch: {}, imageSearch: {} } } });
      } else if (this.imageSearchEnabled && model.supportsImageSearch) {
        tools.push({ google_search: { searchTypes: { imageSearch: {} } } });
      }
      if (tools.length > 0) body.tools = tools;
      if (this.thinkingLevel !== "none") {
        body.generationConfig.thinkingConfig = { thinkingLevel: this.thinkingLevel };
      }
      return body;
    },

    /* ─── BUILD VIDEO REQUEST ─── */
    buildVideoRequest(prompt) {
      const promptObj = { text: prompt };
      if (this.uploadedImageData) {
        promptObj.image = { imageBytes: this.uploadedImageData, mimeType: this.uploadedImageMime };
      }
      return {
        prompt: promptObj,
        generationConfig: {
          durationSeconds: this.veoDuration,
          numberOfVideos: 1,
          aspectRatio: this.veoRatio,
        },
      };
    },

    /* ─── GENERATE VIDEO (Veo LRO) ─── */
    async generateVideo() {
      const prompt = this.promptText.trim();
      if (!prompt || this.isGenerating) return;
      this.isGenerating = true;
      this.isPolling = false;
      this.sidebarCollapsed = true;
      this.errorMessage = "";

      this.$nextTick(() => {
        if (this.$refs.scrollContent) {
          this.$refs.scrollContent.scrollTo({ top: 0, behavior: "smooth" });
        }
      });

      try {
        // Step 1: start the LRO
        const startUrl = `https://generativelanguage.googleapis.com/v1beta/models/${VEO_MODEL.id}:generateVideo?key=${this.API_KEY}`;
        const startRes = await fetch(startUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(this.buildVideoRequest(prompt)),
        });
        if (!startRes.ok) {
          const err = await startRes.json().catch(() => ({}));
          throw new Error(err?.error?.message || `API error ${startRes.status}`);
        }
        const startData = await startRes.json();
        const operationName = startData?.name;
        if (!operationName) throw new Error("No operation name returned from Veo API");

        // Step 2: poll until done (3s intervals, 120s max)
        this.isPolling = true;
        const pollUrl = `https://generativelanguage.googleapis.com/v1beta/${operationName}?key=${this.API_KEY}`;
        const maxAttempts = 40;
        let done = false;
        let videoSrc = null;

        for (let i = 0; i < maxAttempts && !done; i++) {
          await new Promise(r => setTimeout(r, 3000));
          const pollRes = await fetch(pollUrl);
          if (!pollRes.ok) {
            const err = await pollRes.json().catch(() => ({}));
            throw new Error(err?.error?.message || `Poll error ${pollRes.status}`);
          }
          const pollData = await pollRes.json();
          if (pollData.done) {
            done = true;
            const sample = pollData?.response?.generatedSamples?.[0]?.video;
            if (!sample) throw new Error("No video sample in completed operation");
            if (sample.videoBytes) {
              videoSrc = `data:video/mp4;base64,${sample.videoBytes}`;
            } else if (sample.uri) {
              const sep = sample.uri.includes("?") ? "&" : "?";
              const vRes = await fetch(`${sample.uri}${sep}key=${this.API_KEY}`);
              if (!vRes.ok) throw new Error(`Could not fetch video (${vRes.status})`);
              const blob = await vRes.blob();
              videoSrc = URL.createObjectURL(blob);
            }
          }
        }

        if (!done) throw new Error("Video generation timed out (>120s). Please try again.");
        if (!videoSrc) throw new Error("No video data received");

        const now = new Date();
        this.results.unshift({
          video: videoSrc,
          images: [],
          text: "",
          prompt,
          modelName: VEO_MODEL.name,
          ts: Date.now(),
          time: now.toLocaleTimeString(),
          grounded: false,
        });
      } catch (e) {
        this.errorMessage = e.message;
      } finally {
        this.isGenerating = false;
        this.isPolling = false;
        this.$nextTick(() => {
          if (this.$refs.scrollContent) {
            this.$refs.scrollContent.scrollTo({ top: 0, behavior: "smooth" });
          }
        });
      }
    },

    /* ─── GENERATE ─── */
    async generate() {
      if (this.mode === "video") return this.generateVideo();
      const prompt = this.promptText.trim();
      if (!prompt || this.isGenerating) return;
      this.isGenerating = true;
      this.sidebarCollapsed = true;
      this.errorMessage = "";

      this.$nextTick(() => {
        if (this.$refs.scrollContent) {
          this.$refs.scrollContent.scrollTo({ top: 0, behavior: "smooth" });
        }
      });

      try {
        const model = this.currentModel;
        const url = `https://generativelanguage.googleapis.com/v1beta/models/${model.id}:generateContent?key=${this.API_KEY}`;
        const body = this.buildRequestBody(prompt);
        const res = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err?.error?.message || `API error ${res.status}`);
        }
        const data = await res.json();
        const candidate = data?.candidates?.[0];
        if (!candidate) throw new Error("No response candidate from model");
        let images = [];
        let text = "";
        for (const part of (candidate.content?.parts || [])) {
          if (part.text) text += part.text;
          if (part.inlineData) {
            images.push(`data:${part.inlineData.mimeType};base64,${part.inlineData.data}`);
          }
        }
        if (images.length === 0 && !text) throw new Error("No image or text returned");
        const now = new Date();
        this.results.unshift({
          images, text, prompt,
          modelName: model.name,
          ts: Date.now(),
          time: now.toLocaleTimeString(),
          grounded: this.googleSearchEnabled || this.imageSearchEnabled,
        });
      } catch (e) {
        this.errorMessage = e.message;
      } finally {
        this.isGenerating = false;
        this.$nextTick(() => {
          if (this.$refs.scrollContent) {
            this.$refs.scrollContent.scrollTo({ top: 0, behavior: "smooth" });
          }
        });
      }
    },
  },
}).mount('#vueApp');
