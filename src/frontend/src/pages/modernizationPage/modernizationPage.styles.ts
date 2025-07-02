import { makeStyles, tokens } from "@fluentui/react-components";

export const useStyles = makeStyles({
  root: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    // backgroundColor: tokens.colorNeutralBackground2,
  },
  content: {
    display: "flex",
    flex: 1,
    overflow: "hidden",
  },
  fileIcon: {
    color: tokens.colorNeutralForeground1,
    marginRight: "12px",
    flexShrink: 0,
    fontSize: "20px",
    height: "20px",
    width: "20px",
  },
  statusContainer: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginLeft: "auto",
  },
  fileName: {
    flex: 1,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    fontWeight: "600",
  },
  fileList: {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
    padding: "16px",
    flex: 1,
    overflow: "auto",
  },
  panelHeader: {
    padding: "16px 20px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  fileCard: {
    backgroundColor: tokens.colorNeutralBackground1,
    border: `1px solid ${tokens.colorNeutralStroke1}`,
    borderRadius: "4px",
    padding: "12px",
    display: "flex",
    alignItems: "center",
    cursor: "pointer",
    "&:hover": {
      backgroundColor: tokens.colorNeutralBackground3,
      border: tokens.colorBrandBackground,
    },
  },
  selectedCard: {
    border: "var(--NeutralStroke2.Rest)",
    backgroundColor: "#EBEBEB",
  },
  progressFill: {
    height: "100%",
    backgroundColor: "#2563EB",
    transition: "width 0.3s ease",
  },
  imageContainer: {
    display: "flex",
    justifyContent: "center",
    marginTop: "24px",
    marginBottom: "24px",
  },
  stepList: {
    marginTop: "48px",
  },
  step: {
    fontSize: "16px", // Increase font size
    fontWeight: "400", // Make text bold (optional)
    marginBottom: "48px", // Add spacing between steps
  },
  codeCard: {
    backgroundColor: tokens.colorNeutralBackground1,
    boxShadow: tokens.shadow4,
    overflow: "hidden",
    maxHeight: "87vh",
    overflowY: "auto",
  },
  codeHeader: {
    padding: "12px 16px",
  },
  summaryContent: {
    padding: "24px",
  },
  summaryCard: {
    backgroundColor: "#F2FBF2",
    marginBottom: "16px",
    boxShadow: "none"
  },
  errorContent: {
    backgroundColor: "#F8DADB",
    marginBottom: "16px",
    boxShadow: "none"
  },
  errorSection: {
    backgroundColor: "#F8DADB",
    marginBottom: "8px",
    boxShadow: "none"
  },
  warningSection: {
    backgroundColor: tokens.colorStatusWarningBackground1,
    marginBottom: "16px",
    boxShadow: "none"
  },
  warningContent: {
    backgroundColor: tokens.colorStatusWarningBackground1,
    marginBottom: "16px",
    paddingBottom: "22px",
    paddingTop: "8px",
    boxShadow: "none"
  },
  sectionHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    cursor: "pointer",
  },
  errorItem: {
    marginTop: "16px",
    paddingLeft: "20px",
  },
  errorTitle: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginBottom: "8px",
  },
  errorDetails: {
    marginTop: "4px",
    color: tokens.colorNeutralForeground2,
    paddingLeft: "20px",
  },
  errorSource: {
    color: tokens.colorNeutralForeground2,
    fontSize: "12px",
  },
  // Styles for the loading overlay
  loadingOverlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: tokens.colorNeutralBackground1,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 1000,
  },
  loadingCard: {
    width: "100%",
    maxWidth: "500px",
    padding: "32px",
    textAlign: "center",
    boxShadow: tokens.shadow16,
    borderRadius: "8px",
  },
  loadingProgressBar: {
    width: "100%",
    height: "8px",
    backgroundColor: tokens.colorNeutralBackground3,
    borderRadius: "4px",
    marginTop: "24px",
    marginBottom: "8px",
    overflow: "hidden",
  },
  loadingProgressFill: {
    height: "100%",
    backgroundColor: tokens.colorBrandBackground,
    transition: "width 0.5s ease-out",
  },
  mainContent: {
    flex: 1,
    top: "60",
    backgroundColor: "white", // Change from tokens.colorNeutralBackground1 to white
    overflow: "auto",
  },
  progressSection: {
    maxWidth: "800px",
    margin: "20px auto 0", // Add top margin to move it lower in the page
    display: "flex",
    flexDirection: "column",
    paddingTop: "20px", // Add padding at the top
  },
  progressBar: {
    width: "100%",
    height: "4px",
    backgroundColor: "#E5E7EB",
    borderRadius: "2px",
    marginTop: "32px",
    marginBottom: "16px",
    overflow: "hidden",
  },
  buttonContainer: {
    padding: "16px",
    display: "flex",
    justifyContent: "flex-end",
    gap: "8px",
  },
  summaryHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "12px 24px", // Replacing theme.spacing(2) with a fixed value
  },
  summaryTitle: {
    fontSize: "12px",
  },
  aiGeneratedTag: {
    color: "#6b7280", // Replacing theme.palette.text.secondary with a neutral gray
    fontSize: "0.875rem",
    backgroundColor: "#f3f4f6", // Replacing theme.palette.background.default with a light gray
    padding: "4px 8px", // Replacing theme.spacing(0.5, 1)
    borderRadius: "4px", // Replacing theme.shape.borderRadius with a standard value
  },
  queuedFile: {
    borderRadius: "4px",
    backgroundColor: "var(--NeutralBackgroundInvertedDisabled-Rest)", // Correct background color
    opacity: 0.5, // Disabled effect
    pointerEvents: "none", // Prevents clicks
  },
  summaryDisabled: {
    borderRadius: "4px",
    backgroundColor: "var(--NeutralBackgroundInvertedDisabled-Rest)", // Correct background color
    opacity: 0.5, // Disabled effect
    pointerEvents: "none", // Prevents clicks
  },
  inProgressFile: {
    borderRadius: "4px",
    backgroundColor: "var(--NeutralBackground1.Rest)", // Correct background color
    opacity: 0.5, // Disabled effect
  },
  completedFile: {
    borderRadius: "4px",
    backgroundColor: "var(--NeutralBackground1-Rest)", // Correct background color
  },
  downloadButton: {
    marginLeft: "auto",
    display: "flex",
    alignItems: "center",
    gap: "4px",
  },
  errorBanner: {
    backgroundColor: "#F8DADB",
    marginBottom: "16px",
    boxShadow: "none"
  },
  fixedButtonContainer: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0, /* Match your panel background color */
    backgroundColor: tokens.colorNeutralBackground2,
    borderTop: "1px solid #e5e7eb", /* Optional: adds a separator line */
    padding: "0px 16px",
    zIndex: "10",
  },
  panelContainer: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
    position: "relative",
  },
  fileListContainer: {
    flex: 1,
    overflowY: "auto",
    paddingBottom: "60px", /* Add padding to prevent content from being hidden behind the fixed buttons */
  },
  textColor:{
    color: tokens.colorNeutralForeground3,
  },
  loadingContainer:{
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    height: "50vh",
  },
  gettingRedayInfo:{
    marginTop: "16px",
    fontSize: "24px",
    fontWeight: "600" 
  },
  p_20:{
    padding: "20px",
  },
  spinnerCon:{
    padding: "20px",
    textAlign: "center"
  },
  progressText:{
    marginBottom: "20px",
    marginTop: "40px"
  },
  percentageTextContainer:{
    display: "flex",
    justifyContent: "flex-end"
  },
  percentageText:{
    fontWeight: "bold",
    color: "#333"
  },
  progressIcon:{
    width: "160px",
    height: "160px"
  },
  fileLog:{
    display: "flex",
    alignItems: "center"
  },
  fileLogText1:{
    fontSize: "16px",
    marginRight: "4px",
    alignSelf: "flex-start",
  },
  fileLogText2:{
    fontSize: "16px",
    color: "#333",
    marginLeft: "4px",
  },
  loadingText:{
    padding: "20px", 
    textAlign: "center"
  },
  successContainer:{
    textAlign: "center",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    marginTop: "60px",
    height: "50vh",

    img:{
      width: "100px",
      height: "100px",
      marginBottom: "24px",
    }
  },
  mb_24:{
    marginBottom: "24px"  
  },
  mb_16:{
    marginBottom: "16px"
  },
  checkMarkIcon:{
    color: "#0B6A0B",
    width: "16px",
    height: "16px",
  },
  dismissIcon:{
    color: "#BE1100",
    width: "16px",
    height: "16px",
  },
  warningIcon:{
    color: "#B89500",
    width: "16px",
    height: "16px",
  },
  completedIcon:{
    color: "#0B6A0B",
    width: "16px",
    height: "16px",
  }

});