import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from '../../services/apiservice'; // Verifique se o caminho está certo
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-login',
  standalone: true, // Adicionei isso pois você usa imports
  templateUrl: './login.html', // Verifique se o arquivo se chama login.html ou login.component.html
  imports: [CommonModule, FormsModule],
  styleUrls: ['./login.css'] // Verifique se o arquivo existe
})
export class Login {
  email = '';
  password = '';
  erro = '';
  loading = false; // Adicionei para controlar o botão

  constructor(
    private apiService: ApiService,
    private router: Router
  ) {}

  fazerLogin() {
    console.log('1. Clicou em Entrar...');

    if (!this.email || !this.password) {
      this.erro = 'Preencha todos os campos';
      return;
    }

    this.loading = true; // Trava o botão
    this.erro = '';

    const credenciais = { username: this.email, password: this.password };

    this.apiService.login(credenciais).subscribe({
      next: (res: any) => {
        this.loading = false; // Destrava
        
        // 👇 O PULO DO GATO: Vamos ver o que veio!
        console.log('2. Resposta do Servidor (JSON):', res);

        // Verifica se o token existe (com nomes comuns)
        const token = res.access_token || res.token || res.accessToken;

        if (token) {
          console.log('3. Token encontrado:', token);
          
          // Salva o token
          localStorage.setItem('token', token);
          
          console.log('4. Tentando navegar para a Home "/"...');
          
          // Tenta navegar e avisa se der erro
          this.router.navigate(['/']).then(sucesso => {
            if (sucesso) {
              console.log('5. Navegação realizada com sucesso!');
            } else {
              console.error('5. ERRO: A navegação falhou. A rota "/" existe?');
              this.erro = 'Login ok, mas não foi possível redirecionar.';
            }
          });

        } else {
          console.error('3. ERRO: O JSON veio sem token!', res);
          this.erro = 'Erro: Servidor não enviou o token.';
        }
      },
      error: (err: any) => {
        this.loading = false;
        console.error('ERRO GERAL:', err);
        this.erro = 'Usuário ou senha incorretos.';
      }
    });
  }
}