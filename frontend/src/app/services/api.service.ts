import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface TaskStatus {
  status: 'queued' | 'analyzing' | 'rendering' | 'completed' | 'failed';
  progress: number;
  error: string | null;
  video_url: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = 'http://localhost:8000/api';

  constructor(private http: HttpClient) {}

  generateVideo(
    audio: File,
    lyrics: File,
    media: File[],
    options: any,
    fontFile?: File | null
  ): Observable<{ task_id: string }> {
    const formData = new FormData();
    formData.append('audio', audio);
    formData.append('lyrics', lyrics);

    media.forEach((file) => {
      formData.append('media', file);
    });

    if (fontFile) {
      formData.append('font', fontFile);
    }

    formData.append('options', JSON.stringify(options));

    return this.http.post<{ task_id: string }>(`${this.apiUrl}/generate`, formData);
  }

  getStatus(taskId: string): Observable<TaskStatus> {
    return this.http.get<TaskStatus>(`${this.apiUrl}/status/${taskId}`);
  }

  getDownloadUrl(taskId: string): string {
    return `${this.apiUrl}/download/${taskId}`;
  }

  cleanupTask(taskId: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/cleanup/${taskId}`);
  }
}
