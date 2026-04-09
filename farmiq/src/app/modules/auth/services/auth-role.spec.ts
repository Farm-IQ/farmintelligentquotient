import { TestBed } from '@angular/core/testing';

import { AuthRole } from './auth-role';

describe('AuthRole', () => {
  let service: AuthRole;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(AuthRole);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
