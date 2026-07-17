import { defineStore } from "pinia";
import {
  STORAGE_KEYS,
  currentUserId,
  departmentHierarchyMap,
  normalize,
  saveJson,
  splitTags,
} from "../state.js";
import { fetchPeople } from "../services/api/people.js";
import { getMockPeople } from "../services/mock/mockApi.js";
import { isServerMode } from "../services/mode.js";

export const useDirectoryStore = defineStore("directory", {
  state: () => ({
    people: getMockPeople(),
    loaded: false,
    keyword: "",
    filters: {
      level1: "全部一级部门",
      level2: "全部二级部门",
      level3: "全部三级部门",
    },
  }),
  getters: {
    currentUser: (state) => state.people.find((person) => person.id === currentUserId),
    level1Options: (state) => [
      "全部一级部门",
      ...new Set(state.people.map((person) => person.departmentPath[0])),
    ],
    level2Options: (state) => {
      const items = state.people
        .filter((person) => state.filters.level1 === "全部一级部门" || person.departmentPath[0] === state.filters.level1)
        .map((person) => person.departmentPath[1]);
      return ["全部二级部门", ...new Set(items)];
    },
    level3Options: (state) => {
      const items = state.people
        .filter((person) => state.filters.level1 === "全部一级部门" || person.departmentPath[0] === state.filters.level1)
        .filter((person) => state.filters.level2 === "全部二级部门" || person.departmentPath[1] === state.filters.level2)
        .map((person) => person.departmentPath[2]);
      return ["全部三级部门", ...new Set(items)];
    },
    filteredPeople: (state) => {
      const keyword = normalize(state.keyword);
      return state.people.filter((person) => {
        const haystack = normalize([
          person.name,
          person.department,
          person.role,
          person.domains.join(" "),
          person.selfPortrait,
        ].join(" "));
        return (!keyword || haystack.includes(keyword))
          && (state.filters.level1 === "全部一级部门" || person.departmentPath[0] === state.filters.level1)
          && (state.filters.level2 === "全部二级部门" || person.departmentPath[1] === state.filters.level2)
          && (state.filters.level3 === "全部三级部门" || person.departmentPath[2] === state.filters.level3);
      });
    },
  },
  actions: {
    async loadPeople() {
      if (this.loaded && !isServerMode()) return;
      this.people = isServerMode() ? await fetchPeople() : getMockPeople();
      this.loaded = true;
    },
    getPerson(personId) {
      return this.people.find((person) => person.id === personId);
    },
    departmentText(person) {
      return person?.departmentPath?.join(" / ") || person?.department || "";
    },
    resetDepartmentLevel(level) {
      if (level <= 1) this.filters.level2 = "全部二级部门";
      this.filters.level3 = "全部三级部门";
    },
    updatePerson(personId, patch) {
      const person = this.getPerson(personId);
      if (!person) return null;
      const next = { ...patch };
      if (next.domainsText !== undefined) {
        next.domains = splitTags(next.domainsText);
        delete next.domainsText;
      }
      if (next.addDomains) {
        next.domains = Array.from(new Set([...(person.domains || []), ...next.addDomains]));
        delete next.addDomains;
      }
      Object.assign(person, next);
      person.departmentPath = departmentHierarchyMap[person.department] || person.departmentPath;
      if (personId === currentUserId) saveJson(STORAGE_KEYS.profile, person);
      return person;
    },
  },
});
