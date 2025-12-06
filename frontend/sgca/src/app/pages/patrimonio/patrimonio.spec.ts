import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Patrimonio } from './patrimonio';

describe('Patrimonio', () => {
  let component: Patrimonio;
  let fixture: ComponentFixture<Patrimonio>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Patrimonio]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Patrimonio);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
