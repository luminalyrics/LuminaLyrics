import { Component, OnDestroy, ChangeDetectorRef, HostListener } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DecimalPipe, UpperCasePipe } from '@angular/common';
import { ApiService, TaskStatus } from '../../services/api.service';

@Component({
  selector: 'app-generator',
  imports: [FormsModule, DecimalPipe, UpperCasePipe],
  templateUrl: './generator.component.html',
  styleUrl: './generator.component.css'
})
export class GeneratorComponent implements OnDestroy {
  // Files
  audioFile: File | null = null;
  lyricsFile: File | null = null;
  mediaFiles: File[] = [];
  fontFile: File | null = null;

  // Selected Preset & UI State
  selectedPresetId = 'rap';
  showAdvancedSettings = false;

  readonly presets = [
    {
      id: 'rap',
      name: 'RAP & DRILL',
      description: 'Police Impact, fond sombre désaturé, effets glitchs accentués et rythme de beat marqué.',
      badge: 'STYLE RAP',
      options: {
        resolution: '720p',
        fps: 30,
        font_family: 'impact',
        font_size: 48,
        font_color: '#ffffff',
        outline_color: '#000000',
        outline_width: 3,
        karaoke_effect: true,
        text_position: 'bottom',
        text_y_offset: 20,
        visualizer_type: 'bars',
        visualizer_color: '#ffd700', // Yellow
        bass_zoom_sens: 0.8,
        bass_flash_sens: 0.6,
        glitch_sens: 0.5,
        glitch_intensity: 2.0,
        color_filter: 'grayscale',
        beat_interval: 4,
        image_change_prob: 0.8
      }
    },
    {
      id: 'lofi',
      name: 'LO-FI RETRO',
      description: "Police Georgia chaleureuse, couleurs chaudes sépia, visualiseur d'ondes douces et effets apaisés.",
      badge: 'STYLE LO-FI',
      options: {
        resolution: '720p',
        fps: 30,
        font_family: 'georgia',
        font_size: 38,
        font_color: '#f57b42', // Orange
        outline_color: '#111111',
        outline_width: 1,
        karaoke_effect: false,
        text_position: 'middle',
        text_y_offset: 0,
        visualizer_type: 'waveform',
        visualizer_color: '#f57b42',
        bass_zoom_sens: 0.2,
        bass_flash_sens: 0.1,
        glitch_sens: 0.1,
        glitch_intensity: 0.5,
        color_filter: 'sepia',
        beat_interval: 8,
        image_change_prob: 0.4
      }
    },
    {
      id: 'electro',
      name: 'NEON GLITCH',
      description: 'Police Impact, visualiseur circulaire vert fluo, effets de glitchs et zooms de basses extrêmes.',
      badge: 'STYLE NEON',
      options: {
        resolution: '720p',
        fps: 30,
        font_family: 'impact',
        font_size: 56,
        font_color: '#ffffff',
        outline_color: '#000000',
        outline_width: 4,
        karaoke_effect: true,
        text_position: 'bottom',
        text_y_offset: -20,
        visualizer_type: 'circle',
        visualizer_color: '#32a852', // Neon Green
        bass_zoom_sens: 0.7,
        bass_flash_sens: 0.8,
        glitch_sens: 0.8,
        glitch_intensity: 3.5,
        color_filter: 'cool',
        beat_interval: 2,
        image_change_prob: 0.9
      }
    },
    {
      id: 'minimalist',
      name: 'MINIMAL ZEN',
      description: 'Style épuré sans visualiseur, police Arial sans fioritures, pour une mise en valeur brute des images.',
      badge: 'STYLE ZEN',
      options: {
        resolution: '1080p',
        fps: 30,
        font_family: 'arial',
        font_size: 40,
        font_color: '#ffffff',
        outline_color: '#111111',
        outline_width: 2,
        karaoke_effect: false,
        text_position: 'bottom',
        text_y_offset: 40,
        visualizer_type: 'none',
        visualizer_color: '#ffffff',
        bass_zoom_sens: 0.0,
        bass_flash_sens: 0.0,
        glitch_sens: 0.0,
        glitch_intensity: 0.0,
        color_filter: 'none',
        beat_interval: 4,
        image_change_prob: 0.5
      }
    }
  ];

  // Options initialized with default settings
  options = {
    aspect_ratio: '16:9',
    resolution: '720p',
    fps: 30,
    font_family: 'impact',
    font_size: 48,
    font_color: '#ffffff',
    outline_color: '#000000',
    outline_width: 3,
    karaoke_effect: true,
    text_position: 'bottom',
    text_y_offset: 20,
    visualizer_type: 'bars',
    visualizer_color: '#ffd700',
    bass_zoom_sens: 0.8,
    bass_flash_sens: 0.6,
    glitch_sens: 0.5,
    glitch_intensity: 2.0,
    color_filter: 'grayscale',
    beat_interval: 4,
    image_change_prob: 0.8,
  };

  selectPreset(presetId: string) {
    this.selectedPresetId = presetId;
    const preset = this.presets.find(p => p.id === presetId);
    if (preset) {
      const currentAspectRatio = this.options.aspect_ratio;
      this.options = {
        ...this.options,
        ...preset.options,
        aspect_ratio: currentAspectRatio // keep the chosen aspect ratio!
      };
    }
  }

  // Quick B&W toggle (mirrors color_filter)
  get bwToggle(): boolean {
    return this.options.color_filter === 'grayscale';
  }
  set bwToggle(val: boolean) {
    if (val) {
      this._prevColorFilter = this.options.color_filter !== 'grayscale'
        ? this.options.color_filter
        : this._prevColorFilter;
      this.options.color_filter = 'grayscale';
    } else {
      this.options.color_filter = this._prevColorFilter || 'none';
    }
  }
  private _prevColorFilter = 'none';

  // Preset color palette for font
  readonly presetColors = [
    '#ffffff', '#000000', '#32a852', '#f57b42',
    '#ffd700', '#0044ff', '#ff007f', '#4caf50',
    '#9c27b0', '#c0c0c0',
  ];
  readonly presetColorLabels: Record<string, string> = {
    '#ffffff': 'Blanc',
    '#000000': 'Noir',
    '#32a852': 'Vert DA',
    '#f57b42': 'Orange DA',
    '#ffd700': 'Jaune DA',
    '#0044ff': 'Bleu DA',
    '#ff007f': 'Rose',
    '#4caf50': 'Vert Clair',
    '#9c27b0': 'Violet',
    '#c0c0c0': 'Argent',
  };

  // Tabs for customization panel
  activeTab: 'video' | 'lyrics' | 'visualizer' | 'effects' = 'video';

  // Generation status
  currentStep = 1; // 1: Files, 2: Settings, 3: Generation
  isGenerating = false;
  taskId: string | null = null;
  status: 'queued' | 'analyzing' | 'rendering' | 'completed' | 'failed' = 'queued';
  progress = 0;
  errorMsg: string | null = null;
  videoUrl: string | null = null;

  private pollInterval: any = null;

  constructor(private apiService: ApiService, private cdr: ChangeDetectorRef) {}

  // Step Navigation
  nextStep() {
    if (this.currentStep === 1) {
      if (!this.audioFile) {
        alert("Veuillez sélectionner un fichier audio.");
        return;
      }
      if (!this.lyricsFile) {
        alert("Veuillez sélectionner un fichier de paroles (.lrc ou .srt).");
        return;
      }
      if (this.mediaFiles.length === 0) {
        alert("Veuillez ajouter au moins une photo ou une vidéo.");
        return;
      }
      this.currentStep = 2;
    } else if (this.currentStep === 2) {
      this.startGeneration();
    }
  }

  prevStep() {
    if (this.currentStep > 1) {
      this.currentStep--;
    }
  }

  // Set active tab
  setTab(tab: 'video' | 'lyrics' | 'visualizer' | 'effects') {
    this.activeTab = tab;
  }

  // Audio File Handlers
  onAudioSelected(event: any) {
    const file = event.target.files?.[0];
    if (file) {
      this.audioFile = file;
    }
  }

  clearAudio() {
    this.audioFile = null;
  }

  // Lyrics File Handlers
  onLyricsSelected(event: any) {
    const file = event.target.files?.[0];
    if (file) {
      this.lyricsFile = file;
    }
  }

  clearLyrics() {
    this.lyricsFile = null;
  }

  // Media Files Handlers
  onMediaSelected(event: any) {
    const files: FileList = event.target.files;
    if (files) {
      for (let i = 0; i < files.length; i++) {
        this.mediaFiles.push(files[i]);
      }
    }
  }

  removeMedia(index: number) {
    this.mediaFiles.splice(index, 1);
  }

  clearAllMedia() {
    this.mediaFiles = [];
  }

  // Font File Handlers
  onFontSelected(event: any) {
    const file = event.target.files?.[0];
    if (file) {
      this.fontFile = file;
    }
  }

  clearFont() {
    this.fontFile = null;
  }

  // Preset colour selection
  selectPresetColor(color: string) {
    this.options.font_color = color;
  }

  // Drag and Drop helpers
  onDragOver(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
  }

  onAudioDropped(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    const file = event.dataTransfer?.files?.[0];
    if (file && file.type.startsWith('audio/')) {
      this.audioFile = file;
    }
  }

  onLyricsDropped(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    const file = event.dataTransfer?.files?.[0];
    if (file && (file.name.endsWith('.lrc') || file.name.endsWith('.srt') || file.name.endsWith('.txt'))) {
      this.lyricsFile = file;
    }
  }

  onMediaDropped(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    const files = event.dataTransfer?.files;
    if (files) {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        if (file.type.startsWith('image/') || file.type.startsWith('video/')) {
          this.mediaFiles.push(file);
        }
      }
    }
  }

  // Launch Video Generation
  startGeneration() {
    if (!this.audioFile) {
      alert("Veuillez sélectionner un fichier audio.");
      return;
    }
    if (!this.lyricsFile) {
      alert("Veuillez sélectionner un fichier de paroles (.lrc ou .srt).");
      return;
    }
    if (this.mediaFiles.length === 0) {
      alert("Veuillez ajouter au moins une photo ou une vidéo.");
      return;
    }

    this.currentStep = 3;
    this.isGenerating = true;
    this.progress = 0;
    this.status = 'queued';
    this.errorMsg = null;
    this.videoUrl = null;

    this.apiService.generateVideo(
      this.audioFile,
      this.lyricsFile,
      this.mediaFiles,
      this.options,
      this.fontFile
    ).subscribe({
      next: (res) => {
        this.taskId = res.task_id;
        this.pollStatus();
      },
      error: (err) => {
        this.isGenerating = false;
        this.errorMsg = "Impossible de lancer la génération. Vérifiez la connexion avec le serveur.";
        console.error(err);
      }
    });
  }

  // Poll status of the task
  private pollStatus() {
    if (!this.taskId) return;

    this.pollInterval = setInterval(() => {
      this.apiService.getStatus(this.taskId!).subscribe({
        next: (statusData: TaskStatus) => {
          this.status = statusData.status;
          this.progress = statusData.progress;

          if (statusData.status === 'completed') {
            this.videoUrl = this.apiService.getDownloadUrl(this.taskId!);
            this.isGenerating = false;
            this.stopPolling();
          } else if (statusData.status === 'failed') {
            this.errorMsg = statusData.error || "Une erreur inconnue est survenue lors de la génération de la vidéo.";
            this.stopPolling();
          }

          this.cdr.detectChanges();
        },
        error: (err) => {
          this.stopPolling();
          this.errorMsg = "Perte de connexion avec le serveur lors du suivi de la génération.";
          console.error(err);
          this.cdr.detectChanges();
        }
      });
    }, 1000);
  }

  private stopPolling() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  }

  resetApp() {
    this.cleanupCurrentTask();
    
    this.currentStep = 1;
    this.isGenerating = false;
    this.progress = 0;
    this.status = 'queued';
    this.errorMsg = null;
    this.videoUrl = null;
    this.taskId = null;
    this.stopPolling();
    this.selectedPresetId = 'rap';
    this.showAdvancedSettings = false;
    this.options = { aspect_ratio: '16:9', ...this.presets[0].options };
  }

  private cleanupCurrentTask() {
    if (this.taskId) {
      // Call cleanup API
      this.apiService.cleanupTask(this.taskId).subscribe({
        error: (err) => console.error('Erreur lors du nettoyage :', err)
      });
    }
  }

  @HostListener('window:beforeunload', ['$event'])
  unloadHandler(event: Event) {
    if (this.taskId) {
      // Use fetch with keepalive to ensure it fires even when the page is unloading
      fetch(`http://localhost:8000/api/cleanup/${this.taskId}`, {
        method: 'DELETE',
        keepalive: true
      }).catch(err => console.error(err));
    }
  }

  ngOnDestroy() {
    this.stopPolling();
    this.cleanupCurrentTask();
  }
}
