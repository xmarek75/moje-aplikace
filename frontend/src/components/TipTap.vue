<template>
  <editor-content :editor="editor" />
</template>

<script>
import { useEditor, EditorContent } from '@tiptap/vue-3'


export default {
  components: {
    EditorContent
  },

  setup() {
    const editor = useEditor({
      content: '<p>I’m running tiptap with Vue.js. 🎉</p>'
    })

    return { editor }
  }
}
</script>