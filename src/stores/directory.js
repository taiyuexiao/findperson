import { defineStore } from "pinia";
import {
  STORAGE_KEYS,
  currentUserId,
  getActiveUserId,
  departmentHierarchyMap,
  loadJson,
  normalize,
  normalizePersonRecord,
  saveJson,
  splitTags,
} from "../state.js";
import { fetchPeople } from "../services/api/people.js";
import { getMockDepartments, getMockPeople, getMockRoles, saveMockDepartments, saveMockPeople, saveMockRoles } from "../services/mock/mockApi.js";
import { isServerMode } from "../services/mode.js";

const ALL_DEPARTMENTS = "";

export const useDirectoryStore = defineStore("directory", {
  state: () => ({
    people: getMockPeople(),
    departments: getMockDepartments(),
    roles: getMockRoles(),
    activeUserId: getActiveUserId(),
    loaded: false,
    keyword: "",
    filters: { departmentIds: [] },
  }),
  getters: {
    currentUser: (state) => state.people.find((person) => person.id === state.activeUserId),
    activePeople: (state) => state.people.filter((person) => person.active !== false),
    currentUserDepartment: (state) => state.departments.find((department) => department.name === state.people.find((person) => person.id === state.activeUserId)?.department),
    rootDepartments: (state) => state.departments.filter((department) => !department.parentId),
    departmentTree(state) {
      const nodes = new Map(state.departments.map((department) => [department.id, { ...department, children: [] }]));
      const roots = [];
      nodes.forEach((node) => {
        const parent = nodes.get(node.parentId);
        if (parent) parent.children.push(node);
        else roots.push(node);
      });
      return roots;
    },
    departmentFilterLevels() {
      const levels = [];
      let parentId = ALL_DEPARTMENTS;
      let index = 0;
      while (true) {
        const options = parentId
          ? this.departments.filter((department) => department.parentId === parentId)
          : this.rootDepartments;
        if (!options.length) break;
        const selectedId = this.filters.departmentIds[index] || ALL_DEPARTMENTS;
        levels.push({ index, options, selectedId, placeholder: index ? "全部下级部门" : "全部部门" });
        if (!selectedId) break;
        parentId = selectedId;
        index += 1;
      }
      return levels;
    },
    selectedDepartmentId: (state) => state.filters.departmentIds.filter(Boolean).at(-1) || "",
    filteredPeople() {
      const keyword = normalize(this.keyword);
      const selectedId = this.selectedDepartmentId;
      return this.people.filter((person) => {
        const haystack = normalize([
          person.name, person.department, person.role, person.domains.join(" "), person.selfPortrait,
        ].join(" "));
        return (!keyword || haystack.includes(keyword))
          && (!selectedId || this.isDepartmentOrDescendant(person.department, selectedId));
      });
    },
  },
  actions: {
    async loadPeople() {
      if (this.loaded && !isServerMode()) return;
      this.people = isServerMode() ? await fetchPeople() : getMockPeople();
      if (!isServerMode()) this.departments = getMockDepartments();
      if (!isServerMode()) this.roles = getMockRoles();
      this.people.forEach((person) => this.syncPersonDepartmentPath(person));
      this.loaded = true;
    },
    getPerson(personId) { return this.people.find((person) => person.id === personId); },
    getDepartment(reference) {
      return this.departments.find((item) => item.id === reference || item.name === reference);
    },
    childrenOf(departmentId) { return this.departments.filter((item) => item.parentId === departmentId); },
    isDepartmentOrDescendant(departmentRef, ancestorId) {
      let department = this.getDepartment(departmentRef);
      while (department) {
        if (department.id === ancestorId) return true;
        department = department.parentId ? this.getDepartment(department.parentId) : null;
      }
      return false;
    },
    managedDepartments(personId) {
      return this.departments.filter((department) => department.leaderId === personId);
    },
    manageableDepartments(personId) {
      const managedIds = this.managedDepartments(personId).map((department) => department.id);
      return this.departments.filter((department) => managedIds.some((id) => this.isDepartmentOrDescendant(department.id, id)));
    },
    isDepartmentLeader(personId, departmentRef) {
      return this.getDepartment(departmentRef)?.leaderId === personId;
    },
    getPersonSupervisor(personId) {
      const person = this.getPerson(personId);
      let department = this.getDepartment(person?.department);
      while (department) {
        const supervisor = this.getPerson(department.leaderId);
        if (supervisor && supervisor.id !== personId) return { person: supervisor, department };
        department = department.parentId ? this.getDepartment(department.parentId) : null;
      }
      return null;
    },
    setCurrentUser(personId) { this.activeUserId = personId; },
    setDepartmentFilter(level, departmentId) {
      this.filters.departmentIds.splice(level, this.filters.departmentIds.length - level, departmentId || ALL_DEPARTMENTS);
    },
    setDepartmentFilterFromNode(department) {
      const path = [];
      let current = this.getDepartment(department?.id);
      while (current) {
        path.unshift(current.id);
        current = current.parentId ? this.getDepartment(current.parentId) : null;
      }
      this.filters.departmentIds = path;
    },
    resetDepartmentFilters() { this.filters.departmentIds = []; },
    departmentText(person) { return person?.departmentPath?.join(" / ") || person?.department || ""; },
    syncPersonDepartmentPath(person) {
      const department = this.getDepartment(person.department);
      person.departmentPath = department?.path?.slice() || departmentHierarchyMap[person.department] || person.departmentPath;
      return person;
    },
    updatePerson(personId, patch) {
      const person = this.getPerson(personId);
      if (!person) return null;
      const next = { ...patch };
      if (next.domainsText !== undefined) { next.domains = splitTags(next.domainsText); delete next.domainsText; }
      if (next.addDomains) { next.domains = Array.from(new Set([...(person.domains || []), ...next.addDomains])); delete next.addDomains; }
      Object.assign(person, next);
      this.syncPersonDepartmentPath(person);
      if (personId === getActiveUserId()) {
        const profiles = loadJson(STORAGE_KEYS.profile, {});
        saveJson(STORAGE_KEYS.profile, { ...(profiles?.id ? {} : profiles), [personId]: person });
      }
      if (!isServerMode()) saveMockPeople(this.people);
      return person;
    },
    updateDepartment(departmentId, patch) {
      const department = this.getDepartment(departmentId);
      if (!department) return null;
      Object.assign(department, patch);
      if (!isServerMode()) saveMockDepartments(this.departments);
      return department;
    },
    assignDepartmentLeader(departmentId, leaderId) {
      const department = this.getDepartment(departmentId);
      if (!department) return null;
      department.leaderId = leaderId || "";
      if (!isServerMode()) saveMockDepartments(this.departments);
      return department;
    },
    addDepartment({ name, parentId = "", responsibility = "" }) {
      const cleanName = String(name || "").trim();
      const parent = parentId ? this.getDepartment(parentId) : null;
      if (!cleanName || (parentId && !parent) || this.childrenOf(parentId).some((item) => item.name === cleanName)) return null;
      const department = {
        id: `dept-${Date.now()}`,
        name: cleanName,
        parentId,
        path: [...(parent?.path || []), cleanName],
        leaderId: "",
        responsibility,
      };
      this.departments.push(department);
      if (!isServerMode()) saveMockDepartments(this.departments);
      return department;
    },
    addPerson(payload) {
      const department = this.getDepartment(payload.department);
      if (!department || !payload.name?.trim()) return null;
      const person = normalizePersonRecord({
        id: `p-${Date.now()}`, name: payload.name.trim(), department: department.name,
        departmentPath: department.path.slice(), role: payload.role || "专员", contact: payload.contact || "",
        domains: [], selfPortrait: "", peerPortrait: "", completeness: 0, recommendedCount: 0,
        systemRole: payload.systemRole || "普通成员", active: payload.active !== false,
      });
      this.people.push(person);
      if (!isServerMode()) saveMockPeople(this.people);
      return person;
    },
    addRole(name) {
      const role = String(name || "").trim();
      if (!role || this.roles.includes(role)) return false;
      this.roles.push(role);
      if (!isServerMode()) saveMockRoles(this.roles);
      return true;
    },
    removeRole(name) {
      if (this.people.some((person) => person.role === name)) return false;
      this.roles = this.roles.filter((role) => role !== name);
      if (!isServerMode()) saveMockRoles(this.roles);
      return true;
    },
  },
});
