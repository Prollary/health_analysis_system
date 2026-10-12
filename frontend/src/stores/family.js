import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './auth'

export const useFamilyStore = defineStore('family', () => {
  // 当前正在查看的成员 ID（null 表示查看自己）
  const currentMemberId = ref(null)
  const currentMemberName = ref('')
  const members = ref([])

  // 获取实际用于请求的 user_id（查看他人时用成员ID，否则用自己ID）
  function getTargetUserId() {
    const auth = useAuthStore()
    return currentMemberId.value || auth.userId
  }

  function switchMember(id, name) {
    currentMemberId.value = id
    currentMemberName.value = name
  }

  function resetToSelf() {
    currentMemberId.value = null
    currentMemberName.value = ''
  }

  function setMembers(list) {
    members.value = list
  }

  return { currentMemberId, currentMemberName, members, getTargetUserId, switchMember, resetToSelf, setMembers }
})
