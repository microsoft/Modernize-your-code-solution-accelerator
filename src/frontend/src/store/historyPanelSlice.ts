import { createSlice } from "@reduxjs/toolkit";

const historyPanelSlice = createSlice({
  name: "historyPanel",
  initialState: { isOpen: false },
  reducers: {
    togglePanel: (state) => {
      state.isOpen = !state.isOpen;
    },
    openPanel: (state) => {
      state.isOpen = true;
    },
    closePanel: (state) => {
      state.isOpen = false;
    },
  },
});

export const { togglePanel, openPanel, closePanel } = historyPanelSlice.actions;
export default historyPanelSlice.reducer;
