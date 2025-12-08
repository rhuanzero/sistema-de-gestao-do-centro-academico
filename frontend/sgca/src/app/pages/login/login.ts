import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.html',
  styleUrls: ['./login.css']
})
export class Login { // <--- Essa linha é fundamental!
  
  // 1. Injeção de Dependências
  private http = inject(HttpClient);
  private router = inject(Router);

  // 2. Objeto de dados para o formulário
  credenciais = {
    username: '', 
    password: ''
  };

  // 3. Método de Login
  fazerLogin() {
    const formData = new FormData();
    formData.append('username', this.credenciais.username);
    formData.append('password', this.credenciais.password);

    this.http.post('http://localhost:8000/auth/login', formData).subscribe({
      next: (resposta: any) => {
        // --- DEBUG NO CONSOLE ---
        console.log('RESPOSTA DO LOGIN:', resposta); 
        
        // Verifica se o backend mandou o cargo e salva
        if (resposta.cargo) {
            console.log('Salvando cargo:', resposta.cargo);
            localStorage.setItem('user_role', resposta.cargo);
        } else {
            console.warn('Backend sem cargo. Usando fallback.');
            // Fallback temporário para garantir que os botões apareçam
            localStorage.setItem('user_role', 'Presidente'); 
        }

        // Salva o token
        localStorage.setItem('token', resposta.access_token);
        
        // Redireciona
        this.router.navigate(['/membros']);
      },
      error: (err: any) => {
        console.error('Erro no login:', err);
        alert('Login falhou! Verifique suas credenciais.');
      }
    });
  }
}