import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from '../../services/apiservice';
import { CommonModule } from '@angular/common'; // <--- Importe o CommonModule (*ngIf)
import { FormsModule } from '@angular/forms'; // Ajuste o caminho se necessário

@Component({
  selector: 'app-login',
  templateUrl: './login.html',
  imports: [CommonModule, FormsModule],
  styleUrls: ['./login.css']
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
this.apiService.login(this.email, this.password).subscribe({
    next: (response) => {
      localStorage.setItem('token', response.access_token);
      
      // 🔴 ANTES ESTAVA ASSIM (INGLÊS):
      // this.router.navigate(['/members']); 

      // 🟢 MUDE PARA ASSIM (PORTUGUÊS, IGUAL SUA ROTA):
      this.router.navigate(['/membros']); 
    },
    error: (err) => {
      console.error(err);
      this.erro = 'Login falhou! Verifique a senha.';
    }
  });
}
}