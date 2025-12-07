import { Injectable, Inject, PLATFORM_ID } from '@angular/core'; // <--- Importe Inject e PLATFORM_ID
import { isPlatformBrowser } from '@angular/common'; // <--- Importe isPlatformBrowser
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { 
  AuthResponse, 
  Usuario, 
  UsuarioCreate, 
  SaldoResponse, 
  Evento, 
  Patrimonio 
} from '../models/api'; 

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = 'http://127.0.0.1:8000';

  constructor(
    private http: HttpClient,
    @Inject(PLATFORM_ID) private platformId: Object // <--- Injeção para saber onde o código está rodando
  ) { }

  // --- AUXILIAR: PEGAR HEADER COM TOKEN (SEGURA PARA SSR) ---
  private getAuthHeaders(): HttpHeaders {
    let token = '';

    // Verifica se está rodando no Navegador antes de tentar acessar localStorage
    if (isPlatformBrowser(this.platformId)) {
      token = localStorage.getItem('token') || '';
    }

    return new HttpHeaders({
      'Authorization': `Bearer ${token}`
    });
  }

  // --- AUTHENTICATION ---
  login(email: string, password: string): Observable<AuthResponse> {
    const payload = new HttpParams()
      .set('username', email)
      .set('password', password);

    return this.http.post<AuthResponse>(`${this.apiUrl}/auth/login`, payload, {
      headers: new HttpHeaders({ 'Content-Type': 'application/x-www-form-urlencoded' })
    });
  }

  // --- MEMBROS (Usuario) ---
  getMembers(): Observable<Usuario[]> {
    return this.http.get<Usuario[]>(`${this.apiUrl}/members/`, { headers: this.getAuthHeaders() });
  }

  createMember(member: UsuarioCreate): Observable<Usuario> {
    return this.http.post<Usuario>(`${this.apiUrl}/members/`, member, { headers: this.getAuthHeaders() });
  }

  // --- FINANCEIRO ---
  getBalance(): Observable<SaldoResponse> {
    return this.http.get<SaldoResponse>(`${this.apiUrl}/finance/balance`, { headers: this.getAuthHeaders() });
  }

  getTransactions(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/finance/report`, { headers: this.getAuthHeaders() });
  }

  // --- EVENTOS ---
  getEvents(): Observable<Evento[]> {
    return this.http.get<Evento[]>(`${this.apiUrl}/events/`, { headers: this.getAuthHeaders() });
  }

  // --- PATRIMÔNIO ---
  getPatrimony(): Observable<Patrimonio[]> {
    return this.http.get<Patrimonio[]>(`${this.apiUrl}/patrimony/`, { headers: this.getAuthHeaders() });
  }

  // Adicione ou substitua esses métodos:

  // ATUALIZAR (PUT)
  updateMember(id: number, member: any): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/members/${id}`, member, { headers: this.getAuthHeaders() });
  }

  // DELETAR (DELETE)
  deleteMember(id: number): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/members/${id}`, { headers: this.getAuthHeaders() });
  }

  getMe(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/auth/me`, { headers: this.getAuthHeaders() });
  }

  // ... outros métodos ...

  // 👇 ADICIONE ESSA FUNÇÃO QUE ESTÁ FALTANDO
  createTransaction(transacao: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/finance/transactions`, transacao, { headers: this.getAuthHeaders() });
  }

  // --- EVENTOS (MONGODB) ---
  // Criar
  createEvent(evento: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/events/`, evento, { headers: this.getAuthHeaders() });
  }

  // Deletar (Recebe ID como string, pois é MongoID)
  deleteEvent(id: string): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/events/${id}`, { headers: this.getAuthHeaders() });
  }
}


