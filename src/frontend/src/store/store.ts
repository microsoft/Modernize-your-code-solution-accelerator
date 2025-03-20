import { configureStore } from '@reduxjs/toolkit';
import { batchSlice, fileReducer } from '../slices/batchSlice';
import historyPanelReducer from '../slices/historyPanelSlice';

export const store = configureStore({
    reducer: {
        batch: batchSlice.reducer,
        fileUpload: fileReducer,
        historyPanel: historyPanelReducer,
    },
})

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
