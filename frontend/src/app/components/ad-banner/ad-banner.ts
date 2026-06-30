import { Component, AfterViewInit, Input } from '@angular/core';

@Component({
  selector: 'app-ad-banner',
  imports: [],
  templateUrl: './ad-banner.html',
  styleUrl: './ad-banner.css',
})
export class AdBanner implements AfterViewInit {
  @Input() adSlot: string = ''; // L'ID du bloc d'annonce sera passé en paramètre

  ngAfterViewInit(): void {
    try {
      // Indique à Google AdSense de charger l'annonce
      (window as any).adsbygoogle = (window as any).adsbygoogle || [];
      (window as any).adsbygoogle.push({});
    } catch (e) {
      console.error('Erreur lors du chargement de l\\'annonce AdSense:', e);
    }
  }
}
