import api from './api';

export const learningService = {
  async getNextActivity(courseId = null) {
    const params = courseId ? { course_id: courseId } : {};
    const response = await api.get('/learning/next', { params });
    return response.data;
  },

  async submitAttempt(questionId, answer) {
    const response = await api.post('/learning/attempt', {
      question_id: questionId,
      answer: answer,
    });
    return response.data;
  },

  async getHint(questionId, currentAnswer = '') {
    const response = await api.post('/learning/hint', null, {
      params: { question_id: questionId, current_answer: currentAnswer },
    });
    return response.data;
  },
};

export const masteryService = {
  async getMyMastery() {
    const response = await api.get('/mastery');
    return response.data;
  },

  async getStudentMastery(studentId) {
    const response = await api.get(`/mastery/${studentId}`);
    return response.data;
  },

  async getMasteryHistory(studentId) {
    const response = await api.get(`/mastery/${studentId}/history`);
    return response.data;
  },

  async getConceptGraph(studentId = null) {
    const params = studentId ? { student_id: studentId } : {};
    const response = await api.get('/concepts/graph', { params });
    return response.data;
  },

  async getConceptDetail(conceptId, studentId = null) {
    const params = studentId ? { student_id: studentId } : {};
    const response = await api.get(`/concepts/${conceptId}`, { params });
    return response.data;
  },
};
