import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';
import { Evento, Patrimonio } from '../models/api'; 


@Injectable({
  providedIn: 'root'
})
export class ApiService {
  
  private baseUrl = 'http://127.0.0.1:8000';

  constructor(
    private http: HttpClient,
    private router: Router
  ) {}

 login(credenciais: any): Observable<any> {
    // Transforma o JSON em formato de formulário (username=...&password=...)
    const body = new HttpParams()
      .set('username', credenciais.username) // O FastAPI exige o campo 'username'
      .set('password', credenciais.password);

    return this.http.post(`${this.baseUrl}/auth/login`, body.toString(), {
      headers: new HttpHeaders().set('Content-Type', 'application/x-www-form-urlencoded')
    });
  }

  logout() {
    localStorage.removeItem('token');
    this.router.navigate(['/login']);
  }

  getUser(): Observable<any> {
    return this.http.get(`${this.baseUrl}/auth/me`);
  }

  // --- EVENTOS ---
  getEventos(): Observable<Evento[]> {
    return this.http.get<Evento[]>(`${this.baseUrl}/events/`);
  }

  // Aceita 'any' na criação para não reclamar da falta de ID
  createEvento(evento: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/events/`, evento);
  }

  // O componente estava chamando deleteEvent, mas aqui era deleteEvento.
  // Vamos manter o padrão deleteEvento e corrigir no componente.
  deleteEvento(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/events/${id}`);
  }

  // ... (mantenha os outros métodos de evento/patrimonio que já funcionavam)

  // --- MEMBROS (Faltava isso!) ---
  getMembers(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/users/`); 
  }

  createMember(member: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/auth/register`, member); 
  }

  updateMember(id: string, data: any): Observable<any> {
    return this.http.put(`${this.baseUrl}/users/${id}`, data);
  }

  deleteMember(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/users/${id}`);
  }

  // --- FINANCEIRO (Faltava isso!) ---
  getBalance(): Observable<any> {
    // Exemplo de rota
    return this.http.get(`${this.baseUrl}/financeiro/balance`);
  }

  getTransactions(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/financeiro/transactions`);
  }

  createTransaction(transaction: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/financeiro/transactions`, transaction);
  }

  deletePatrimonio(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/patrimonio/${id}`);
  }

  getPatrimonios(): Observable<Patrimonio[]> {
    return this.http.get<Patrimonio[]>(`${this.baseUrl}/patrimonio/`);
  }

createPatrimonio(item: any): Observable<any> {
    const payload = {
      // Campos de Texto (garante string)
      nome: String(item.nome),
      tombo: item.tombo ? String(item.tombo) : '', 
      localizacao: item.localizacao ? String(item.localizacao) : 'Não informado',
      descricao: 'Item cadastrado via sistema', // O Backend provavelmente exige esse campo!
      
      // Campo de Valor (garante número float)
      valor: parseFloat(item.valor), 

      // Campo de Status (Mapeia 'estado' do front para 'status' do back)
      status: item.estado, 
      
      // Campo de Data (Garante YYYY-MM-DD)
      data_aquisicao: new Date().toISOString().split('T')[0]
    };

    console.log('Enviando Payload:', payload); // Debug no console do navegador

    return this.http.post(`${this.baseUrl}/patrimonio/`, payload);
  }

  // Faça o mesmo para o UPDATE se necessário
  updatePatrimonio(id: string, item: any): Observable<any> {
    const payload = {
      ...item, // Copia tudo
      status: item.estado, // Garante o campo status
      // Se precisar converter data de novo, faça aqui
    };
    // Remove o campo 'estado' se o backend for chato e não aceitar campos extras
    delete payload.estado; 
    
    return this.http.put(`${this.baseUrl}/patrimonio/${id}`, payload);
  }
}