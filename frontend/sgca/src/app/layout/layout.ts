import { Component } from '@angular/core';
import { RouterOutlet, RouterLink } from '@angular/router';
// Importe seu componente de Menu aqui se for usar, ex: import { SidebarComponent } ...

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [RouterOutlet, RouterLink], // <--- Importante
  templateUrl: './layout.html',
  styleUrl: './layout.css'
})
export class Layout {}