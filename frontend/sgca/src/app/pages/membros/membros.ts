import { Component, OnInit, Inject, PLATFORM_ID } from '@angular/core'; // <--- 1. Importe Inject e PLATFORM_ID
import { CommonModule, isPlatformBrowser } from '@angular/common'; // <--- 2. Importe isPlatformBrowser
import { ApiService } from '../../services/apiservice';
import { Usuario } from '../../models/api';

@Component({
  selector: 'app-membros',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './membros.html',
  styleUrl: './membros.css'
})
export class Membros implements OnInit {
  membros: Usuario[] = [];

  constructor(
    private api: ApiService,
    @Inject(PLATFORM_ID) private platformId: Object // <--- 3. Injete o identificador da plataforma
  ) {}

  ngOnInit() {
    // 4. BLOQUEIO: Se não for navegador (for servidor), NÃO FAZ NADA.
    if (isPlatformBrowser(this.platformId)) {
      
      // Aqui dentro é seguro, estamos no Chrome/Firefox/etc
      this.api.getMembers().subscribe({
        next: (data) => {
          this.membros = data;
          console.log('Membros carregados:', data);
        },
        error: (err) => console.error('Erro ao carregar membros:', err)
      });

    }
  }
}