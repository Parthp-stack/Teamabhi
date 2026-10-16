import api from './api';

export const learningService = {
  // Phase 2 Adaptive Question Endpoint
  async getNextQuestion(courseId = null) {
    const params = courseId ? { course_id: courseId } : {};
    const response = await api.get('/questions/next', { params });
    return response.data;
  },

  // Submit Answer to Question
  async submitAttempt(questionId, selectedAnswer, timeTaken = 0.0) {
    const response = await api.post(`/questions/${questionId}/attempt`, {
      selected_answer: selectedAnswer,
      time_taken: timeTaken,
    });
    return response.data;
  },

  // Dynamic Learning Path
  async getLearningPath() {
    const response = await api.get('/learning/path');
    return response.data;
  },

  // Student Mastery Overview
  async getStudentMastery() {
    const response = await api.get('/student/mastery');
    return response.data;
  },

  // Weak Concepts
  async getWeakConcepts() {
    const response = await api.get('/student/weak-concepts');
    return response.data;
  },

  // Interactive Concept Graph for React Flow
  async getConceptGraph(studentId = null) {
    const params = studentId ? { student_id: studentId } : {};
    const response = await api.get('/concepts/graph', { params });
    return response.data;
  },

  // Concept Detail
  async getConceptDetail(conceptId, studentId = null) {
    const params = studentId ? { student_id: studentId } : {};
    const response = await api.get(`/concepts/${conceptId}`, { params });
    return response.data;
  },

  async getMyMastery() {
    const response = await api.get('/student/mastery');
    return response.data;
  },

  // Phase 4: Mastery Analytics
  async getAnalytics() {
    const response = await api.get('/student/analytics');
    return response.data;
  },

  // Phase 4: Student Assessment History
  async getAssessmentHistory() {
    const response = await api.get('/student/assessments');
    return response.data;
  },

  // Phase 4: Coding Assessment History & Explain Your Code Results
  async getCodingHistory() {
    const response = await api.get('/student/coding-history');
    return response.data;
  },
};

export const masteryService = learningService;

export const aiService = {
  async explainConcept(concept, studentMastery = 0.0, difficulty = 'MEDIUM') {
    const response = await api.post('/ai/explain-concept', {
      concept,
      student_mastery: studentMastery,
      difficulty,
    });
    return response.data;
  },

  async generateQuestion(concept, difficulty = 'MEDIUM', questionType = 'MCQ') {
    const response = await api.post('/ai/generate-question', {
      concept,
      difficulty,
      question_type: questionType,
    });
    return response.data;
  },

  async generatePractice(concept, studentWeakAreas = []) {
    const response = await api.post('/ai/generate-practice', {
      concept,
      student_weak_areas: studentWeakAreas,
    });
    return response.data;
  },
};

export const trainerService = {
  async getBasicOverview(params = {}) {
    const response = await api.get('/trainer/overview', { params });
    return response.data;
  },

  async getDashboardOverview(params = {}) {
    const response = await api.get('/trainer/dashboard', { params });
    return response.data;
  },

  async getStudentDeepDive(studentId) {
    const response = await api.get(`/trainer/student/${studentId}`);
    return response.data;
  },

  // Curriculum Management
  async getCurriculum() {
    const response = await api.get('/trainer/curriculum');
    return response.data;
  },

  async createCourse(data) {
    const response = await api.post('/trainer/courses', data);
    return response.data;
  },

  async updateCourse(id, data) {
    const response = await api.put(`/trainer/courses/${id}`, data);
    return response.data;
  },

  async createModule(data) {
    const response = await api.post('/trainer/modules', data);
    return response.data;
  },

  async createConcept(data) {
    const response = await api.post('/trainer/concepts', data);
    return response.data;
  },

  async updateConcept(id, data) {
    const response = await api.put(`/trainer/concepts/${id}`, data);
    return response.data;
  },

  async deleteConcept(id) {
    const response = await api.delete(`/trainer/concepts/${id}`);
    return response.data;
  },

  async addPrerequisite(conceptId, prereqId) {
    const response = await api.post(`/trainer/concepts/${conceptId}/prerequisites`, {
      prerequisite_id: prereqId,
    });
    return response.data;
  },

  async removePrerequisite(conceptId, prereqId) {
    const response = await api.delete(`/trainer/concepts/${conceptId}/prerequisites/${prereqId}`);
    return response.data;
  },

  // Question Bank
  async getQuestionBank(params = {}) {
    const response = await api.get('/trainer/questions', { params });
    return response.data;
  },

  async createQuestion(data) {
    const response = await api.post('/trainer/questions', data);
    return response.data;
  },

  async updateQuestion(id, data) {
    const response = await api.put(`/trainer/questions/${id}`, data);
    return response.data;
  },

  async deleteQuestion(id) {
    const response = await api.delete(`/trainer/questions/${id}`);
    return response.data;
  },

  async previewAIQuestion(data) {
    const response = await api.post('/trainer/questions/ai-preview', data);
    return response.data;
  },

  // Optional Feature: GitHub Repo Evaluator
  async analyzeGitHubRepo(repoUrl) {
    const response = await api.post(`/trainer/repo-evaluation/analyze?repo_url=${encodeURIComponent(repoUrl)}`);
    return response.data;
  },

  async evaluateRepoViva(answersPayload) {
    const response = await api.post('/trainer/repo-evaluation/viva', answersPayload);
    return response.data;
  },

  // Optional Feature: DevOps Lab
  async verifyDevOpsLab(taskId, solutionCode) {
    const response = await api.post('/coding/devops-lab/verify', {
      task_id: taskId,
      solution_code: solutionCode,
    });
    return response.data;
  },
};
