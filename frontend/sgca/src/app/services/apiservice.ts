import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  
  private baseUrl = 'http://127.0.0.1:8000';

  constructor(
    private http: HttpClient,
    private router: Router
  ) {}

  // ==========================================================
  // 🔐 AUTENTICAÇÃO (AUTH)
  // ==========================================================

  login(credenciais: any): Observable<any> {
    const body = new HttpParams()
      .set('username', credenciais.username)
      .set('password', credenciais.password);

    return this.http.post(`${this.baseUrl}/auth/login`, body.toString(), {
      headers: new HttpHeaders().set('Content-Type', 'application/x-www-form-urlencoded')
    });
  }

  getUser(): Observable<any> {
    return this.http.get(`${this.baseUrl}/auth/me`);
  }

  logout() {
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem('token');
    }
    this.router.navigate(['/login']);
  }

  // ==========================================================
  // 📢 COMUNICAÇÃO (POSTS E SOLICITAÇÕES) - 👇 ATUALIZADO AQUI
  // ==========================================================

  getPosts(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/communication/posts`);
  }

  createPost(post: any): Observable<any> {
    const payload = {
      titulo: post.titulo,
      conteudo_texto: post.conteudo_texto || 'Sem conteúdo',
      midia_destino: post.midia_destino,
      data_agendamento: post.data_agendamento,
      anexos: [] 
    };
    return this.http.post(`${this.baseUrl}/communication/create_posts`, payload);
  }

  // 👇 ESSE É O MÉTODO QUE FALTAVA (updatePost)
  updatePost(id: string, post: any): Observable<any> {
    return this.http.put(`${this.baseUrl}/communication/posts/${id}`, post);
  }

  getRequests(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/communication/requests`);
  }

  createRequest(req: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/communication/requests`, req);
  }

  // 👇 ESSE É O QUE DEU O ERRO (updateRequest)
  updateRequest(id: string, req: any): Observable<any> {
    return this.http.put(`${this.baseUrl}/communication/requests/${id}`, req);
  }

  // ==========================================================
  // 📦 PATRIMÔNIO
  // ==========================================================

  getPatrimonios(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/patrimonio/`);
  }

  createPatrimonio(item: any): Observable<any> {
    const payload = {
      nome: String(item.nome),
      tombo: item.tombo ? String(item.tombo) : '',
      valor: parseFloat(item.valor) || 0,
      localizacao: item.localizacao ? String(item.localizacao) : 'Não informado',
      descricao: item.descricao || 'Item cadastrado via sistema',
      status: item.estado || 'Disponível',
      data_aquisicao: new Date().toISOString().split('T')[0]
    };
    return this.http.post(`${this.baseUrl}/patrimonio/`, payload);
  }

  updatePatrimonio(id: string, item: any): Observable<any> {
    const payload = { ...item };
    if (item.estado) payload.status = item.estado;
    return this.http.put(`${this.baseUrl}/patrimonio/${id}`, payload);
  }

  deletePatrimonio(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/patrimonio/${id}`);
  }

  // ==========================================================
  // 📅 EVENTOS
  // ==========================================================

  getEventos(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/events/`);
  }

  createEvento(evento: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/events/`, evento);
  }

  updateEvento(id: string, evento: any): Observable<any> {
    return this.http.put(`${this.baseUrl}/events/${id}`, evento);
  }

  deleteEvento(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/events/${id}`);
  }

  // ==========================================================
  // 💰 FINANCEIRO
  // ==========================================================

  getBalance(): Observable<any> {
    return this.http.get(`${this.baseUrl}/financeiro/balance`);
  }

  getTransactions(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/financeiro/transactions`);
  }

  createTransaction(transaction: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/financeiro/transactions`, transaction);
  }

  // ==========================================================
  // 👥 MEMBROS (USUÁRIOS)
  // ==========================================================

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
}