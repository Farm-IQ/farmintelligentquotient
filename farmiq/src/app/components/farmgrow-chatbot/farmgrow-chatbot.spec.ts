import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FarmgrowChatbot } from './farmgrow-chatbot';

describe('FarmgrowChatbot', () => {
  let component: FarmgrowChatbot;
  let fixture: ComponentFixture<FarmgrowChatbot>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FarmgrowChatbot]
    })
    .compileComponents();

    fixture = TestBed.createComponent(FarmgrowChatbot);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
