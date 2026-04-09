import { TestBed } from '@angular/core/testing';

import { FarmgrowChatbotService } from './farmgrow-chatbot.service';

describe('FarmgrowChatbotService', () => {
  let service: FarmgrowChatbotService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(FarmgrowChatbotService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
