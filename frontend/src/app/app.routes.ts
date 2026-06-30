import { Routes } from '@angular/router';
import { HomeComponent } from './pages/home/home.component';
import { GeneratorComponent } from './pages/generator/generator.component';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'create', component: GeneratorComponent },
  { path: '**', redirectTo: '' }
];
