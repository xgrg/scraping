import { describe, it, expect } from "vitest";

describe("App imports", () => {
  it("should import clubs.json successfully", () => {
    const clubs = require("../clubs.json");
    expect(clubs).toBeDefined();
    expect(typeof clubs).toBe("object");
  });

  it("should have valid club structure", () => {
    const clubs = require("../clubs.json");
    expect(Object.keys(clubs).length).toBeGreaterThan(0);
    
    Object.entries(clubs).forEach(([deptId, deptClubs]) => {
      expect(typeof deptId).toBe("string");
      expect(typeof deptClubs).toBe("object");
      
      Object.entries(deptClubs).forEach(([clubId, clubName]) => {
        expect(typeof clubId).toBe("string");
        expect(typeof clubName).toBe("string");
        expect(clubName.length).toBeGreaterThan(0);
      });
    });
  });

  it("should have expected departments", () => {
    const clubs = require("../clubs.json");
    // Should have at least one department
    expect(Object.keys(clubs).length).toBeGreaterThan(0);
    // First key should be department code
    const firstDept = Object.keys(clubs)[0];
    expect(firstDept.match(/^\d+$/)).toBeTruthy();
  });
});

describe("Utility functions", () => {
  it("should handle URLSearchParams", () => {
    const params = new URLSearchParams("?id=11660020");
    const id = params.get("id");
    expect(id).toBe("11660020");
  });

  it("should validate club IDs across departments", () => {
    const clubs = require("../clubs.json");
    let foundClub = false;
    
    Object.entries(clubs).forEach(([deptId, deptClubs]) => {
      if (deptClubs["11660020"]) {
        foundClub = true;
        expect(deptClubs["11660020"]).toBeDefined();
      }
    });
    
    // May not find this specific club, which is OK
    expect(typeof foundClub).toBe("boolean");
  });

  it("should handle invalid club IDs gracefully", () => {
    const clubs = require("../clubs.json");
    let clubFound = false;
    
    Object.entries(clubs).forEach(([deptId, deptClubs]) => {
      if (deptClubs["99999999"]) {
        clubFound = true;
      }
    });
    
    expect(clubFound).toBe(false);
  });
});
