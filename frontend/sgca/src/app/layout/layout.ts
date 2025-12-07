import { Component, OnInit, ChangeDetectorRef } from '@angular/core'; // <--- Importe ChangeDetectorRef
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ApiService } from '../services/apiservice'; // Ajuste o caminho do seu service

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './layout.html',
  styleUrls: ['./layout.css']
})
export class Layout implements OnInit {
  nomeUsuario: string = 'Carregando...';
  menuAberto: boolean = false; // Exemplo de outra variável que vc pode ter

  constructor(
    private authService: ApiService,
    private cdRef: ChangeDetectorRef // <--- Injete o ChangeDetectorRef aqui
  ) {}

  ngOnInit(): void {
    // Exemplo de como você busca o usuário
    this.authService.getUser().subscribe({
      next: (user) => {
        if (user && user.nome) {
          this.nomeUsuario = user.nome;
          
          // O PULO DO GATO: Força o Angular a atualizar a tela agora
          this.cdRef.detectChanges(); 
        }
      },
      error: () => {
        this.nomeUsuario = 'Visitante';
        this.cdRef.detectChanges();
      }
    });
  }

  logout() {
    this.authService.logout();
  }
}