import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from '../services/apiservice'; // Ajuste o caminho se necessário

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class Login {
  email = '';
  password = '';
  erro = '';

  constructor(
    private apiService: ApiService,
    private router: Router
  ) {}

  fazerLogin() {
    // Limpa erro anterior
    this.erro = '';

    this.apiService.login(this.email, this.password).subscribe({
      next: (response) => {
        // 1. O Backend devolveu o token
        console.log('Login sucesso!', response);

        // 2. Guardamos no localStorage (CRUCIAL)
        // O nome 'token' deve ser igual ao que está no getAuthHeaders() do seu Service
        localStorage.setItem('token', response.access_token);

        // 3. Redireciona para a página de membros
        this.router.navigate(['/members']); 
      },
      error: (err) => {
        console.error(err);
        this.erro = 'E-mail ou senha incorretos!';
      }
    });
  }
}